#!/usr/bin/env python3
import PyPDF2
import sys

pdf_path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/teste.pdf'

print(f"\n{'='*70}")
print(f"🔍 TESTANDO EXTRAÇÃO DE PDF")
print(f"{'='*70}\n")

try:
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)

        print(f"📄 Total de páginas: {len(reader.pages)}")
        print(f"\n{'='*70}")
        print("📝 AMOSTRA DA PÁGINA 1:")
        print(f"{'='*70}\n")

        # Extrair texto da primeira página
        page1 = reader.pages[0]
        texto = page1.extract_text()

        # Mostrar primeiras 1000 caracteres
        print(texto[:1000])

        print(f"\n{'='*70}")
        print("✅ EXTRAÇÃO POSSÍVEL!")
        print(f"{'='*70}\n")

except Exception as e:
    print(f"\n❌ ERRO: {e}\n")
    print("⚠️  PDF pode estar protegido ou ser imagem escaneada")
    print("   Vamos precisar de OCR para esse arquivo\n")
