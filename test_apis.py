#!/usr/bin/env python3
"""
Script de prueba para validar las API Keys del .env
- 4 claves de Gemini (usando gemini-2.5-flash-preview-04-17)
- 1 clave NVIDIA NIM para Kimi K2 (moonshotai/kimi-k2-instruct)
"""

import os
import sys

# ========== CONFIGURACIÓN DE CLAVES ==========
GEMINI_KEYS = {
    "GEMINI_CV_API_KEY":   "AIzaSyA-mRmxqrcU1d9ECX2964PxmnOv_X8f2DM",
    "GEMINI_API_KEY_1":    "AIzaSyDxxMwEEVDokY1VBNFm1q9_-ARBaTXdTW8",
    "GEMINI_API_KEY_2":    "AIzaSyBeTllOT7ql6Jr81PBTMiJ9I9iegmpACp8",
    "GEMINI_API_KEY_3":    "AIzaSyBZgd7mIANhNg1ZjsVnekGb3zldrtqRVx8",
}

NVIDIA_API_KEY = "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"

# Modelos a usar
GEMINI_MODEL = "gemini-2.5-flash"
KIMI_MODEL   = "moonshotai/kimi-k2-instruct"

PROMPT_TEST  = "Responde solo: '¡API OK!'"

# ================================================

def test_gemini_key(name, api_key):
    """Prueba una clave de Gemini usando la librería google-generativeai."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(PROMPT_TEST)
        text = response.text.strip()
        print(f"  ✅  {name}: ACTIVA  → Respuesta: {text[:60]}")
        return True
    except Exception as e:
        error_msg = str(e)
        # Resumir el mensaje de error
        if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
            reason = "API Key inválida o revocada"
        elif "quota" in error_msg.lower() or "ResourceExhausted" in error_msg:
            reason = "Cuota agotada (API válida pero sin créditos)"
        elif "not found" in error_msg.lower() or "404" in error_msg:
            reason = f"Modelo '{GEMINI_MODEL}' no encontrado — verifica el nombre"
        else:
            reason = error_msg[:120]
        print(f"  ❌  {name}: INACTIVA → {reason}")
        return False


def test_nvidia_kimi(api_key):
    """Prueba la clave NVIDIA NIM para Kimi K2 con la API compatible con OpenAI."""
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )
        response = client.chat.completions.create(
            model=KIMI_MODEL,
            messages=[{"role": "user", "content": PROMPT_TEST}],
            max_tokens=50,
        )
        text = response.choices[0].message.content.strip()
        print(f"  ✅  MOONSHOT_API_KEY (Kimi K2): ACTIVA  → Respuesta: {text[:60]}")
        return True
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg or "invalid" in error_msg.lower():
            reason = "API Key inválida o revocada"
        elif "402" in error_msg or "insufficient" in error_msg.lower() or "quota" in error_msg.lower():
            reason = "Sin créditos en la cuenta NVIDIA NIM"
        elif "404" in error_msg or "not found" in error_msg.lower():
            reason = f"Modelo '{KIMI_MODEL}' no encontrado en NVIDIA NIM"
        else:
            reason = error_msg[:120]
        print(f"  ❌  MOONSHOT_API_KEY (Kimi K2): INACTIVA → {reason}")
        return False


def check_dependencies():
    """Verifica que las librerías necesarias estén instaladas."""
    missing = []
    try:
        import google.generativeai
    except ImportError:
        missing.append("google-generativeai")
    try:
        from openai import OpenAI
    except ImportError:
        missing.append("openai")

    if missing:
        print(f"⚠️  Faltan dependencias: {', '.join(missing)}")
        print(f"   Instala con: pip install {' '.join(missing)}")
        sys.exit(1)


def main():
    print("=" * 65)
    print("   🔑  VALIDACIÓN DE API KEYS")
    print("=" * 65)

    check_dependencies()

    # ---- Gemini ----
    print(f"\n📌 GEMINI  (modelo: {GEMINI_MODEL})")
    print("-" * 65)
    gemini_ok = 0
    for name, key in GEMINI_KEYS.items():
        if test_gemini_key(name, key):
            gemini_ok += 1

    # ---- NVIDIA / Kimi K2 ----
    print(f"\n🚀 NVIDIA NIM  (modelo: {KIMI_MODEL})")
    print("-" * 65)
    nvidia_ok = test_nvidia_kimi(NVIDIA_API_KEY)

    # ---- Resumen ----
    print("\n" + "=" * 65)
    print(f"   RESUMEN: Gemini {gemini_ok}/{len(GEMINI_KEYS)} activas | "
          f"NVIDIA {'✅' if nvidia_ok else '❌'}")
    print("=" * 65)


if __name__ == "__main__":
    main()
