import base64
import os
from pathlib import Path
import re
import subprocess
import sys


def value(name: str) -> str:
    return os.environ.get(name, "").strip()


def configure_keystore(android_root: Path) -> tuple[str, str, Path]:
    alias = value("ANDROID_KEY_ALIAS")
    password = value("ANDROID_KEY_PASSWORD")
    encoded = value("ANDROID_KEY_BASE64")
    keystore = Path(value("RUNNER_TEMP") or ".") / "scholarpulse-release.jks"

    if encoded:
        if not alias or not password:
            raise SystemExit("ANDROID_KEY_ALIAS and ANDROID_KEY_PASSWORD are required with ANDROID_KEY_BASE64")
        keystore.write_bytes(base64.b64decode("".join(encoded.split())))
    else:
        alias = alias or "scholarpulse-release"
        commit = value("GITHUB_SHA")[:12] or "local-build"
        password = password or f"ScholarPulse-{commit}!"
        keystore.unlink(missing_ok=True)
        subprocess.run(
            [
                "keytool",
                "-genkeypair",
                "-storetype",
                "JKS",
                "-keystore",
                str(keystore),
                "-storepass",
                password,
                "-keypass",
                password,
                "-alias",
                alias,
                "-keyalg",
                "RSA",
                "-keysize",
                "2048",
                "-validity",
                "10000",
                "-dname",
                "CN=ScholarPulse, OU=ScholarPulse, O=Soheil Aghayani, C=US",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )

    properties = android_root / "keystore.properties"
    properties.write_text(
        "password={password}\nkeyAlias={alias}\nstoreFile={store}\n".format(
            password=password,
            alias=alias,
            store=keystore.as_posix(),
        ),
        encoding="utf-8",
    )
    return alias, password, keystore


def patch_gradle(android_root: Path) -> None:
    gradle = android_root / "app" / "build.gradle.kts"
    if not gradle.exists():
        raise SystemExit(f"Generated Gradle file not found: {gradle}")

    text = gradle.read_text(encoding="utf-8")
    for import_line in ("import java.io.FileInputStream", "import java.util.Properties"):
        if import_line not in text:
            text = f"{import_line}\n{text}"

    signing_config = '''    signingConfigs {
        create("release") {
            val keystorePropertiesFile = rootProject.file("keystore.properties")
            val keystoreProperties = Properties()
            if (keystorePropertiesFile.exists()) {
                keystoreProperties.load(FileInputStream(keystorePropertiesFile))
            }
            keyAlias = keystoreProperties["keyAlias"] as String
            keyPassword = keystoreProperties["password"] as String
            storeFile = file(keystoreProperties["storeFile"] as String)
            storePassword = keystoreProperties["password"] as String
        }
    }'''
    if 'create("release")' not in text:
        match = re.search(r"(?m)^(\s*)buildTypes\s*\{", text)
        if not match:
            raise SystemExit("Could not find the generated Android buildTypes block")
        text = text[: match.start()] + signing_config + "\n\n" + text[match.start() :]

    assignment = 'signingConfig = signingConfigs.getByName("release")'
    if assignment not in text:
        release_block = re.search(r'(?m)^(\s*)(?:getByName\("release"\)|release)\s*\{', text)
        if release_block:
            insert_at = release_block.end()
            text = text[:insert_at] + f"\n{release_block.group(1)}    {assignment}" + text[insert_at:]
        else:
            build_types = re.search(r"(?m)^(\s*)buildTypes\s*\{", text)
            if not build_types:
                raise SystemExit("Could not add the Android release signing config")
            indent = build_types.group(1)
            block = f'{indent}    getByName("release") {{\n{indent}        {assignment}\n{indent}    }}\n'
            text = text[: build_types.end()] + "\n" + block + text[build_types.end() :]

    gradle.write_text(text, encoding="utf-8")
    print(f"Configured Android release signing in {gradle}")


def main() -> None:
    android_root = Path(sys.argv[1] if len(sys.argv) > 1 else "src-tauri/gen/android")
    configure_keystore(android_root)
    patch_gradle(android_root)


if __name__ == "__main__":
    main()
