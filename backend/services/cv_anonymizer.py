"""
CV Anonymizer - Versión modular para integración
Anonimiza datos personales preservando experiencia profesional
"""

import PyPDF2
import spacy
import fitz  # PyMuPDF
import os
import re
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
    
    def extract_personal_data(self, pdf_path: str) -> PersonalData:
        """
        Extrae datos personales del PDF (sin incluir nombres)
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            PersonalData con todos los datos encontrados (excepto nombres)
        """
        if self.verbose:
            print(f"📄 Analizando: {os.path.basename(pdf_path)}")
        
        # Extraer texto
        text = self._extract_text(pdf_path)
        
        # Extraer metadatos
        metadata, metadata_issues = self._analyze_metadata(pdf_path)
        
        # Detectar datos personales en contenido (sin nombres)
        names = []  # No detectar nombres
        phones = self._detect_phones(text)
        emails = self._detect_emails(text)
        
        return PersonalData(
            names=names,
            phones=phones,
            emails=emails,
            metadata_issues=metadata_issues
        )
    
    def anonymize(self, pdf_path: str, output_name: Optional[str] = None) -> AnonymizationResult:
        """
        Anonimiza un CV completo
        
        Args:
            pdf_path: Ruta al PDF original
            output_name: Nombre del archivo de salida (opcional)
            
        Returns:
            AnonymizationResult con el resultado del proceso
        """
        try:
            # Extraer datos personales
            personal_data = self.extract_personal_data(pdf_path)
            
            # Verificar si hay datos para anonimizar (sin incluir nombres)
            total_personal = len(personal_data.phones) + len(personal_data.emails)
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
                    'names_found': 0,  # Los nombres no se anonimizan
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
        # Buscar nombres personales
        name_pattern = r'\b([A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+\s+[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+)\b'
        names = re.findall(name_pattern, text)
        
        for name in names:
            if self._is_valid_personal_name(name):
                return True
        
        # Buscar emails
        if re.search(self.email_pattern, text, re.IGNORECASE):
            return True
            
        return False
    
    def _detect_personal_names(self, text: str) -> List[str]:
        """Detecta nombres personales en el texto de forma más agresiva"""
        candidates = set()
        
        # spaCy NER - Solo si está disponible
        if self.nlp is not None:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == 'PER' and len(ent.text.strip()) > 1:
                    # Limpiar y normalizar el nombre detectado por spaCy
                    name = ent.text.strip()
                    # Remover caracteres no deseados pero mantener acentos
                    name = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ]', ' ', name)
                    name = ' '.join(name.split())  # Normalizar espacios
                    if len(name) > 1:
                        candidates.add(name)
        
        # Búsqueda en todo el documento, no solo las primeras líneas
        lines = text.split('\n')
        
        # Patrón muy agresivo para nombres (cualquier combinación de palabras capitalizadas)
        name_patterns = [
            # Nombres completos (2+ palabras capitalizadas)
            r'\b([A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+(?:\s+[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+)+)\b',
            # Nombres al inicio de línea
            r'^([A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+(?:\s+[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+)*)',
            # Nombres después de "Nombre:", "Name:", etc.
            r'(?:nombre|name|apellidos?)\s*:?\s*([A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+(?:\s+[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]+)*)',
        ]
        
        # Buscar en las primeras 20 líneas (donde suelen estar los nombres)
        first_lines = '\n'.join(lines[:20])
        
        for pattern in name_patterns:
            matches = re.findall(pattern, first_lines, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                name = match.strip()
                if len(name) > 1:
                    candidates.add(name)
        
        # También buscar nombres sueltos (una sola palabra) que puedan ser nombres propios
        single_name_pattern = r'\b([A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]{2,15})\b'
        single_matches = re.findall(single_name_pattern, first_lines)
        for name in single_matches:
            if self._could_be_first_name(name):
                candidates.add(name)
        
        # Filtrar nombres válidos con criterios muy relajados
        valid_names = [name for name in candidates if self._is_valid_name_relaxed(name)]
        
        # Eliminar duplicados/contenidos
        filtered_names = self._filter_duplicate_names(valid_names)
        
        if self.verbose and filtered_names:
            print(f"🔍 Nombres detectados: {filtered_names}")
        
        return filtered_names
    
    def _could_be_first_name(self, word: str) -> bool:
        """Verifica si una palabra podría ser un nombre propio"""
        word = word.strip()
        
        # Lista básica de nombres comunes españoles para ayudar en la detección
        common_first_names = {
            'maría', 'carmen', 'ana', 'isabel', 'pilar', 'dolores', 'teresa', 'laura',
            'cristina', 'marta', 'patricia', 'sandra', 'elena', 'sara', 'paula',
            'antonio', 'manuel', 'francisco', 'david', 'josé', 'juan', 'javier',
            'daniel', 'carlos', 'miguel', 'alejandro', 'fernando', 'sergio', 'pablo',
            'jorge', 'rafael', 'ángel', 'andrés', 'alberto', 'luis', 'rubén',
            'adrián', 'iván', 'raúl', 'víctor', 'roberto', 'pedro', 'marcos'
        }
        
        word_lower = word.lower()
        
        # Si está en la lista de nombres comunes
        if word_lower in common_first_names:
            return True
        
        # Si tiene características de nombre (3-15 caracteres, empezar con mayúscula)
        if (3 <= len(word) <= 15 and 
            word[0].isupper() and 
            word[1:].islower() and
            word.isalpha()):
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

    def _is_valid_personal_name(self, name: str) -> bool:
        """Valida si es un nombre personal real (función de compatibilidad)"""
        return self._is_valid_name_relaxed(name)
    
    def _is_valid_personal_name_improved(self, name: str) -> bool:
        """Función de compatibilidad"""
        return self._is_valid_name_relaxed(name)
    
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
    
    def _detect_emails(self, text: str) -> List[str]:
        """Detecta direcciones de email"""
        emails = re.findall(self.email_pattern, text, re.IGNORECASE)
        return [email.strip() for email in emails]
    
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
            
            # Anonimizar contenido si es necesario (sin incluir nombres)
            total_content_data = len(personal_data.phones) + len(personal_data.emails)
            
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
        """Anonimiza el contenido del PDF en todas las páginas (sin incluir nombres)"""
        doc = fitz.open(pdf_path)
        
        # Preparar reemplazos (sin nombres)
        replacements = []
        
        # No anonimizar nombres
        # for name in personal_data.names:
        #     replacements.append((name, self.replacements['name']))
        
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


def anonymize_cv(pdf_path: str, verbose: bool = False, custom_replacements: Optional[Dict[str, str]] = None, output_name: Optional[str] = None) -> AnonymizationResult:
    """
    Función de conveniencia para anonimizar un CV
    
    Args:
        pdf_path: Ruta al archivo PDF
        verbose: Si mostrar información detallada
        custom_replacements: Reemplazos personalizados
        output_name: Nombre del archivo de salida
        
    Returns:
        AnonymizationResult con el resultado
    """
    anonymizer = CVAnonymizer(verbose=verbose, custom_replacements=custom_replacements)
    return anonymizer.anonymize(pdf_path, output_name)


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