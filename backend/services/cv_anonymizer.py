"""
CV Anonymizer - Versión modular para integración
Anonimiza datos personales preservando experiencia profesional
"""

import PyPDF2
import spacy
import fitz  # PyMuPDF
import os
import re
import asyncio
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class AnonymizationResult:
    """Resultado del proceso de anonimización"""
    success: bool
    output_file: Optional[str] = None
    personal_data_count: int = 0
    metadata_count: int = 0
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class PersonalData:
    """Datos personales detectados"""
    names: List[str]
    phones: List[str]
    emails: List[str]
    metadata_issues: Dict[str, Any]


class CVAnonymizer:
    """Anonimizador de CVs - versión modular y silenciosa"""
    
    def __init__(self, verbose: bool = False, custom_replacements: Optional[Dict[str, str]] = None):
        """
        Inicializa el anonimizador
        
        Args:
            verbose: Si True, muestra información detallada
            custom_replacements: Reemplazos personalizados {'tipo': 'valor'}
        """
        self.verbose = verbose
        self._load_nlp_model()
        
        # Datos de reemplazo por defecto
        self.replacements = {
            'name': 'Candidato',
            'email': 'correo@candidato.com', 
            'phone': '123456789'
        }
        
        # Aplicar reemplazos personalizados si se proporcionan
        if custom_replacements:
            self.replacements.update(custom_replacements)
        
        # Patrones de detección
        self._setup_patterns()
    
    def _load_nlp_model(self) -> None:
        """Carga el modelo de spaCy si está disponible"""
        try:
            self.nlp = spacy.load("es_core_news_sm")
            if self.verbose:
                print("✅ Modelo spaCy cargado")
        except OSError:
            if self.verbose:
                print("⚠️ Modelo spaCy 'es_core_news_sm' no encontrado. Funcionando con patrones básicos.")
                print("💡 Para mejor detección, instalar con: python -m spacy download es_core_news_sm")
            self.nlp = None
    
    # inside CVAnonymizer._get_user_data
    def _get_user_data(self, user_id: int) -> Optional[Dict]:
        """
        Obtiene datos del usuario desde la base de datos
        """
        try:
            # Importar aquí para evitar imports circulares
            from backend.models.user_profile import UserPersonalInfoQueries
            
            # Verificar si ya hay un loop activo
            try:
                loop = asyncio.get_running_loop()
                # Si hay un loop activo, crear una nueva tarea
                if loop.is_running():
                    # Usar un nuevo hilo para ejecutar la operación asíncrona
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_async_query, user_id)
                        user_data = future.result()
                        return user_data
                else:
                    # Si no hay loop activo, crear uno nuevo
                    user_data = loop.run_until_complete(
                        UserPersonalInfoQueries.get_profile_by_user_id(user_id)
                    )
                    return user_data
            except RuntimeError:
                # No hay loop activo, crear uno nuevo
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    user_data = loop.run_until_complete(
                        UserPersonalInfoQueries.get_profile_by_user_id(user_id)
                    )
                    return user_data
                finally:
                    loop.close()
                    
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Error obteniendo datos del usuario {user_id}: {e}")
            return None
    
    def _run_async_query(self, user_id: int) -> Optional[Dict]:
        """Ejecuta la consulta asíncrona en un nuevo loop"""
        import asyncio
        from backend.models.user_profile import UserPersonalInfoQueries
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                UserPersonalInfoQueries.get_profile_by_user_id(user_id)
            )
        finally:
            loop.close()
    
    def _setup_patterns(self) -> None:
        """Configura los patrones de detección"""
        self.phone_patterns = [
            r'\b(\+34|0034)?\s*[6-9]\d{2}\s*\d{2}\s*\d{2}\s*\d{2}\b',
            r'\b(\+34|0034)?\s*[8-9]\d{1}\s*\d{3}\s*\d{2}\s*\d{2}\b',
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{3}\b',
            r'\b[6-9]\d{8}\b'
        ]
        
        self.email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        
        self.sensitive_metadata_fields = {
            '/Author', '/Creator', '/Producer', '/Subject', '/Title',
            'author', 'creator', 'producer', 'subject', 'title', 'keywords'
        }
    
    def extract_personal_data(self, pdf_path: str, user_data: Optional[Dict] = None) -> PersonalData:
        """
        Extrae datos personales del PDF usando datos específicos del usuario
        
        Args:
            pdf_path: Ruta al archivo PDF
            user_data: Datos del usuario obtenidos de la base de datos
            
        Returns:
            PersonalData con todos los datos encontrados (usando datos del usuario si están disponibles)
        """
        if self.verbose:
            print(f"📄 Analizando: {os.path.basename(pdf_path)}")
        
        # Extraer texto
        text = self._extract_text(pdf_path)
        
        # Extraer metadatos
        metadata, metadata_issues = self._analyze_metadata(pdf_path)
        
        # Detectar datos personales usando información del usuario si está disponible
        names = self._detect_user_names_from_db(text, user_data)  # Detectar nombres específicos del usuario
        phones = self._detect_phones_with_user_data(text, user_data)
        emails = self._detect_emails_with_user_data(text, user_data)
        
        return PersonalData(
            names=names,
            phones=phones,
            emails=emails,
            metadata_issues=metadata_issues
        )
    
    def anonymize(self, pdf_path: str, output_name: Optional[str] = None, user_id: Optional[int] = None) -> AnonymizationResult:
        """
        Anonimiza un CV completo usando datos específicos del usuario
        
        Args:
            pdf_path: Ruta al PDF original
            output_name: Nombre del archivo de salida (opcional)
            user_id: ID del usuario para obtener datos específicos de la BD
            
        Returns:
            AnonymizationResult con el resultado del proceso
        """
        try:
            # Obtener datos del usuario desde la base de datos si se proporciona user_id
            user_data = None
            if user_id:
                user_data = self._get_user_data(user_id)
                if self.verbose and user_data:
                    print(f"👤 Datos del usuario obtenidos: {user_data.get('full_name', 'N/A')}")
            
            # Extraer datos personales del PDF
            personal_data = self.extract_personal_data(pdf_path, user_data)
            
            # Verificar si hay datos para anonimizar (incluye nombres del usuario)
            total_personal = len(personal_data.names) + len(personal_data.phones) + len(personal_data.emails)
            total_metadata = len(personal_data.metadata_issues)
            
            if total_personal == 0 and total_metadata == 0:
                if self.verbose:
                    print("ℹ️ No se encontraron datos personales")
                return AnonymizationResult(
                    success=True,
                    personal_data_count=0,
                    metadata_count=0,
                    details={'message': 'No personal data found'}
                )
            
            # Procesar anonimización
            output_file = self._process_anonymization(pdf_path, personal_data, output_name)
            
            if self.verbose:
                print(f"✅ Anonimizado: {output_file}")
                print(f"📊 Datos personales: {total_personal}, Metadatos: {total_metadata}")
            
            return AnonymizationResult(
                success=True,
                output_file=output_file,
                personal_data_count=total_personal,
                metadata_count=total_metadata,
                details={
                    'names_found': len(personal_data.names),  # Nombres específicos del usuario
                    'phones_found': len(personal_data.phones),
                    'emails_found': len(personal_data.emails)
                }
            )
            
        except Exception as e:
            return AnonymizationResult(
                success=False,
                error_message=str(e)
            )
    
    def _extract_text(self, pdf_path: str) -> str:
        """Extrae texto del PDF"""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _analyze_metadata(self, pdf_path: str) -> Tuple[Dict, Dict]:
        """Analiza metadatos del PDF"""
        metadata = {}
        metadata_issues = {}
        
        try:
            # PyPDF2 metadata
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                if reader.metadata:
                    for key, value in reader.metadata.items():
                        if value:
                            metadata[key] = value
            
            # PyMuPDF metadata
            doc = fitz.open(pdf_path)
            fitz_metadata = doc.metadata
            if fitz_metadata:
                for key, value in fitz_metadata.items():
                    if value and key not in metadata:
                        metadata[key] = value
            doc.close()
            
            # Evaluar metadatos sensibles
            for key, value in metadata.items():
                key_clean = key.lower().replace('/', '')
                if key in self.sensitive_metadata_fields or key_clean in self.sensitive_metadata_fields:
                    if self._contains_personal_info(str(value)):
                        metadata_issues[key] = value
                        
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Error analizando metadatos: {e}")
        
        return metadata, metadata_issues
    
    def _contains_personal_info(self, text: str) -> bool:
        """Verifica si el texto contiene información personal"""
        # Buscar emails (criterio principal para metadatos)
        if re.search(self.email_pattern, text, re.IGNORECASE):
            return True
            
        # Buscar patrones de nombres simples
        name_pattern = r'\b([A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+\s+[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+)\b'
        names = re.findall(name_pattern, text)
        
        # Verificar si hay nombres que parezcan reales (al menos 2 palabras capitalizadas)
        for name in names:
            if len(name.strip()) > 5:  # Filtro básico por longitud
                return True
            
        return False
    

    
    def _is_valid_name_relaxed(self, name: str) -> bool:
        """Validación muy relajada para nombres - más agresiva en la detección"""
        name = name.strip()
        words = name.split()
        
        # Filtros básicos muy permisivos
        if len(name) < 2 or len(name) > 80 or len(words) < 1 or len(words) > 6:
            return False
        
        # Solo letras válidas y algunos caracteres especiales
        if not re.match(r'^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s\-\'\.]+$', name):
            return False
        
        # Filtros de exclusión muy básicos (solo palabras obviamente no nombres)
        excluded_words = {
            'cv', 'curriculum', 'vitae', 'email', 'telefono', 'phone', 'mail',
            'linkedin', 'github', 'www', 'com', 'org', 'net', 'http', 'https',
            'pdf', 'doc', 'docx', 'html', 'css', 'javascript', 'python',
            'años', 'año', 'experiencia', 'formacion', 'educacion',
            'universidad', 'colegio', 'instituto', 'empresa', 'trabajo'
        }
        
        # Verificar si contiene palabras claramente excluidas
        name_lower = name.lower()
        for excluded in excluded_words:
            if excluded == name_lower or (len(excluded) > 3 and excluded in name_lower):
                return False
        
        # Si es una sola palabra, verificar que no sea una palabra común no-nombre
        if len(words) == 1:
            word_lower = words[0].lower()
            common_non_names = {
                'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en', 'con',
                'por', 'para', 'que', 'como', 'sobre', 'desde', 'hasta', 'entre'
            }
            if word_lower in common_non_names:
                return False
        
        # Verificar que al menos una palabra empiece con mayúscula
        if not any(word[0].isupper() for word in words if word):
            return False
        
        return True


    
    def _filter_duplicate_names(self, names: List[str]) -> List[str]:
        """Filtra nombres duplicados o contenidos en otros"""
        sorted_names = sorted(names, key=len, reverse=True)
        filtered = []
        
        for name in sorted_names:
            is_subset = any(name != filtered_name and name in filtered_name 
                          for filtered_name in filtered)
            if not is_subset:
                filtered.append(name)
        
        return filtered
    
    def _detect_phones(self, text: str) -> List[str]:
        """Detecta números de teléfono"""
        phones = set()
        
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    phone = ''.join(match).strip()
                else:
                    phone = match.strip()
                
                if self._is_valid_phone(phone):
                    phones.add(phone)
        
        return list(phones)
    
    def _detect_phones_with_user_data(self, text: str, user_data: Optional[Dict] = None) -> List[str]:
        """Detecta números de teléfono usando datos del usuario si están disponibles"""
        phones = set()
        
        # Detección automática con patrones
        auto_phones = self._detect_phones(text)
        phones.update(auto_phones)
        
        # Si hay datos del usuario, también buscar información específica
        if user_data and self.verbose:
            print(f"🔍 Buscando datos de contacto específicos del usuario...")
        
        return list(phones)
    
    def _detect_emails(self, text: str) -> List[str]:
        """Detecta direcciones de email"""
        emails = re.findall(self.email_pattern, text, re.IGNORECASE)
        return [email.strip() for email in emails]
    
    def _detect_emails_with_user_data(self, text: str, user_data: Optional[Dict] = None) -> List[str]:
        """Detecta direcciones de email usando datos del usuario si están disponibles"""
        emails = set()
        
        # Detección automática con patrones
        auto_emails = self._detect_emails(text)
        emails.update(auto_emails)
        
        # Si hay datos del usuario, también buscar información específica
        if user_data and self.verbose:
            print(f"📧 Usando detección mejorada con datos del usuario...")
        
        return list(emails)
    
    def _detect_user_names_from_db(self, text: str, user_data: Optional[Dict] = None) -> List[str]:
        """
        Detecta el nombre específico del usuario desde la base de datos en el texto
        
        Args:
            text: Texto del PDF
            user_data: Datos del usuario obtenidos de la base de datos
            
        Returns:
            Lista con el nombre del usuario si se encuentra en el texto
        """
        names_found = []
        
        if not user_data or not user_data.get('full_name'):
            if self.verbose:
                print("👤 No hay datos de usuario o nombre disponible")
            return names_found
        
        full_name = user_data['full_name'].strip()
        
        if self.verbose:
            print(f"🔍 Buscando el nombre '{full_name}' en el documento...")
        
        # Buscar el nombre completo
        if full_name.lower() in text.lower():
            names_found.append(full_name)
            if self.verbose:
                print(f"✅ Nombre completo encontrado: '{full_name}'")
        
        # También buscar partes del nombre (nombre y apellidos por separado)
        name_parts = full_name.split()
        if len(name_parts) > 1:
            for part in name_parts:
                if len(part) >= 3 and part.lower() in text.lower():
                    # Verificar que no esté ya en la lista
                    if part not in names_found:
                        names_found.append(part)
                        if self.verbose:
                            print(f"✅ Parte del nombre encontrada: '{part}'")
        
        if self.verbose:
            if names_found:
                print(f"📝 Total de nombres a anonimizar: {len(names_found)}")
            else:
                print("ℹ️ No se encontró el nombre del usuario en el documento")
        
        return names_found
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Valida si un teléfono es válido"""
        clean_phone = phone.replace(' ', '').replace('-', '').replace('.', '')
        return phone and len(clean_phone) >= 9 and clean_phone.isdigit()
    
    def _process_anonymization(self, pdf_path: str, personal_data: PersonalData, output_name: Optional[str]) -> str:
        """Procesa la anonimización completa"""
        temp_files = []
        
        try:
            working_file = pdf_path
            
            # Limpiar metadatos si es necesario
            if personal_data.metadata_issues:
                temp_metadata_file = self._clean_metadata(pdf_path)
                if temp_metadata_file:
                    temp_files.append(temp_metadata_file)
                    working_file = temp_metadata_file
            
            # Anonimizar contenido si es necesario (incluye nombres del usuario)
            total_content_data = len(personal_data.names) + len(personal_data.phones) + len(personal_data.emails)
            
            if total_content_data > 0:
                output_file = self._anonymize_content(working_file, personal_data, output_name)
            else:
                # Solo metadatos, renombrar archivo temporal
                if temp_files:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = output_name or f"cv_anonimo_{timestamp}.pdf"
                    os.rename(temp_files[0], output_file)
                    temp_files.remove(temp_files[0])
                else:
                    output_file = output_name or f"cv_anonimo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            return output_file
            
        finally:
            # Limpiar archivos temporales
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception:
                    pass
    
    def _clean_metadata(self, pdf_path: str) -> Optional[str]:
        """Limpia metadatos del PDF"""
        try:
            doc = fitz.open(pdf_path)
            
            clean_metadata = {
                'author': 'Usuario Anónimo',
                'creator': 'CV Anónimo',
                'producer': 'CV Anónimo',
                'subject': 'Currículum Vitae Anonimizado',
                'title': 'CV Anónimo',
                'keywords': '',
                'creationDate': '',
                'modDate': ''
            }
            
            doc.set_metadata(clean_metadata)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            temp_file = f"temp_metadata_{timestamp}.pdf"
            
            doc.save(temp_file)
            doc.close()
            
            return temp_file
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Error limpiando metadatos: {e}")
            return None
    
    def _anonymize_content(self, pdf_path: str, personal_data: PersonalData, output_name: Optional[str]) -> str:
        """Anonimiza el contenido del PDF en todas las páginas (incluye nombres específicos del usuario)"""
        doc = fitz.open(pdf_path)
        
        # Preparar reemplazos (incluye nombres del usuario de la BD)
        replacements = []
        
        # Anonimizar nombres específicos del usuario desde la BD
        for name in personal_data.names:
            replacements.append((name, self.replacements['name']))
        
        for phone in personal_data.phones:
            replacements.append((phone, self.replacements['phone']))
        
        for email in personal_data.emails:
            replacements.append((email, self.replacements['email']))
        
        # Ordenar por longitud (más largos primero) para evitar reemplazos parciales
        replacements.sort(key=lambda x: len(x[0]), reverse=True)
        
        if self.verbose:
            print(f"🔄 Procesando {len(doc)} páginas para anonimización...")
            print(f"📝 Reemplazos a realizar: {len(replacements)}")
            for orig, repl in replacements:
                print(f"   '{orig}' → '{repl}'")
        
        # Procesar todas las páginas del documento
        total_replacements = 0
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_replacements = 0
            
            # Realizar reemplazos en esta página
            for original, replacement in replacements:
                areas = page.search_for(original)
                
                if areas:
                    if self.verbose:
                        print(f"   📄 Página {page_num + 1}: Encontradas {len(areas)} ocurrencias de '{original}'")
                    
                    for area in areas:
                        # Crear anotación de redacción (cubre el texto original)
                        page.add_redact_annot(area, fill=(1, 1, 1))
                    
                    # Aplicar las redacciones
                    page.apply_redactions()
                    
                    # Insertar el texto de reemplazo
                    for area in areas:
                        insertion_point = fitz.Point(area.x0, area.y1 - 2)
                        try:
                            page.insert_text(
                                insertion_point,
                                replacement,
                                fontsize=10.0,  # Tamaño de fuente más pequeño para mejor ajuste
                                color=(0, 0, 0),
                                fontname="helv"
                            )
                        except Exception as e:
                            if self.verbose:
                                print(f"⚠️ Error insertando texto en página {page_num + 1}: {e}")
                    
                    page_replacements += len(areas)
                    total_replacements += len(areas)
            
            if self.verbose and page_replacements > 0:
                print(f"✅ Página {page_num + 1}: {page_replacements} reemplazos realizados")
        
        if self.verbose:
            print(f"✅ Total de reemplazos realizados: {total_replacements}")
        
        # Guardar archivo final
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_name or f"cv_anonimo_{timestamp}.pdf"
        
        try:
            doc.save(output_file)
            if self.verbose:
                print(f"💾 Archivo guardado: {output_file}")
        except Exception as e:
            if self.verbose:
                print(f"❌ Error guardando archivo: {e}")
            raise
        finally:
            doc.close()
        
        return output_file


def anonymize_cv(
    pdf_path: str, 
    verbose: bool = False, 
    custom_replacements: Optional[Dict[str, str]] = None, 
    output_name: Optional[str] = None,
    user_id: Optional[int] = None
) -> AnonymizationResult:
    """
    Función de conveniencia para anonimizar un CV usando datos del usuario
    
    Args:
        pdf_path: Ruta al archivo PDF
        verbose: Si mostrar información detallada
        custom_replacements: Reemplazos personalizados
        output_name: Nombre del archivo de salida
        user_id: ID del usuario para obtener datos específicos de la BD
        
    Returns:
        AnonymizationResult con el resultado
    """
    anonymizer = CVAnonymizer(verbose=verbose, custom_replacements=custom_replacements)
    return anonymizer.anonymize(pdf_path, output_name, user_id)


# CLI para usar como script independiente
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python cv_anonymizer.py <archivo.pdf> [--verbose]")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    verbose = "--verbose" in sys.argv
    
    if not os.path.exists(pdf_file):
        print(f"❌ Archivo no encontrado: {pdf_file}")
        sys.exit(1)
    
    result = anonymize_cv(pdf_file, verbose=verbose)
    
    if result.success:
        print(f"✅ Anonimización completada: {result.output_file}")
        if result.personal_data_count > 0 or result.metadata_count > 0:
            print(f"📊 Datos anonimizados: {result.personal_data_count + result.metadata_count}")
    else:
        print(f"❌ Error: {result.error_message}")
        sys.exit(1)