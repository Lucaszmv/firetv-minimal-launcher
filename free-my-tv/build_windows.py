import os
import re
import subprocess
import shutil
import sys


def _version(name):
    return [int(p) for p in re.findall(r"\d+", name)]


def _newest(parent, pattern):
    """Newest entry (by version) under `parent` that matches `pattern` relative path."""
    found = [os.path.join(parent, d, pattern) for d in os.listdir(parent)
             if os.path.exists(os.path.join(parent, d, pattern))]
    return max(found, key=_version) if found else None


SDK = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or \
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "android-sdk")
JAVA = os.environ.get("JAVA_HOME") or ""
AJ = _newest(os.path.join(SDK, "platforms"), "android.jar") if os.path.isdir(os.path.join(SDK, "platforms")) else None
BT = None
if os.path.isdir(os.path.join(SDK, "build-tools")):
    BT = os.path.join(SDK, "build-tools", max(os.listdir(os.path.join(SDK, "build-tools")), key=_version))
if not AJ or not BT:
    sys.exit("Android SDK nao encontrado: defina ANDROID_HOME (e instale build-tools + platform)")
AAPT2 = os.path.join(BT, "aapt2.exe")
JAVAC = os.path.join(JAVA, "bin", "javac.exe") if JAVA else (shutil.which("javac") or "javac")
JAVA_BIN = os.path.join(JAVA, "bin", "java.exe") if JAVA else (shutil.which("java") or "java")
JAR_BIN = os.path.join(JAVA, "bin", "jar.exe") if JAVA else (shutil.which("jar") or "jar")
D8 = os.path.join(BT, "d8.bat")
ZIPALIGN = os.path.join(BT, "zipalign.exe")
APKSIGNER = os.path.join(BT, "apksigner.bat")

here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)

os.makedirs("out/gen/io/freemytv", exist_ok=True)
os.makedirs("out/classes", exist_ok=True)

print("1. aapt2 compile res...")
subprocess.run([AAPT2, "compile", "--dir", "app/res", "-o", "out/res.zip"], check=True)

print("2. aapt2 link...")
if os.path.exists("out/base.apk"):
    os.remove("out/base.apk")
subprocess.run([
    AAPT2, "link", "-o", "out/base.apk", "-I", AJ,
    "--manifest", "app/AndroidManifest.xml",
    "--java", "out/gen", "out/res.zip",
    "--min-sdk-version", "26", "--target-sdk-version", "33",
    "-A", "app/assets", "-0", "ttf"
], check=True)

print("3. Executando FixAssets.java oficial...")
fix_code = """import java.nio.file.*;
import java.util.zip.*;

class FixAssets {
    public static void main(String[] args) throws Exception {
        Path apk = Paths.get(args[0]);
        Path tmp = apk.resolveSibling(apk.getFileName() + ".fixed");
        int renamed = 0;
        try (ZipInputStream in = new ZipInputStream(Files.newInputStream(apk));
             ZipOutputStream out = new ZipOutputStream(Files.newOutputStream(tmp))) {
            for (ZipEntry e; (e = in.getNextEntry()) != null; ) {
                byte[] data = in.readAllBytes();
                String name = e.getName().replace('\\\\', '/');
                if (!name.equals(e.getName())) renamed++;
                ZipEntry n = new ZipEntry(name);
                if (e.getMethod() == ZipEntry.STORED) {
                    n.setMethod(ZipEntry.STORED);
                    n.setSize(data.length);
                    n.setCompressedSize(data.length);
                    CRC32 crc = new CRC32();
                    crc.update(data);
                    n.setCrc(crc.getValue());
                }
                out.putNextEntry(n);
                out.write(data);
                out.closeEntry();
            }
        }
        if (renamed > 0) Files.move(tmp, apk, StandardCopyOption.REPLACE_EXISTING);
        else Files.delete(tmp);
        System.out.println("FixAssets: renamed " + renamed + " asset paths in " + apk.getFileName());
    }
}
"""
with open("out/FixAssets.java", "w", encoding="utf-8") as f:
    f.write(fix_code)

subprocess.run([JAVAC, "out/FixAssets.java"], check=True)
subprocess.run([JAVA_BIN, "-cp", "out", "FixAssets", "out/base.apk"], check=True)

print("4. Javac...")
java_files = []
for root, _, files in os.walk("app/src"):
    for f in files:
        if f.endswith(".java"):
            java_files.append(os.path.join(root, f))
for root, _, files in os.walk("out/gen"):
    for f in files:
        if f.endswith(".java"):
            java_files.append(os.path.join(root, f))

bootcp = f"{AJ};{BT}\\core-lambda-stubs.jar"
cmd_javac = [
    JAVAC, "-nowarn", "-Xlint:-options", "-source", "8", "-target", "8", "-parameters",
    "-bootclasspath", bootcp, "-classpath", AJ, "-encoding", "UTF-8", "-d", "out/classes"
] + java_files
r = subprocess.run(cmd_javac, capture_output=True, text=True)
if r.returncode != 0:
    print("Javac failed:\n", r.stderr)
    sys.exit(1)

print("5. d8...")
class_files = []
for root, _, files in os.walk("out/classes"):
    for f in files:
        if f.endswith(".class"):
            class_files.append(os.path.join(root, f))
subprocess.run([D8, "--release", "--min-api", "26", "--lib", AJ, "--output", "out"] + class_files, check=True)

print("6. Adicionando classes.dex...")
subprocess.run([JAR_BIN, "-u", "-M", "-f", "out/base.apk", "-C", "out", "classes.dex"], check=True)

print("7. zipalign...")
if os.path.exists("out/aligned.apk"):
    os.remove("out/aligned.apk")
subprocess.run([ZIPALIGN, "-f", "-p", "4", "out/base.apk", "out/aligned.apk"], check=True)

print("8. apksigner...")
if os.path.exists("FreeMyTV.apk"):
    os.remove("FreeMyTV.apk")
subprocess.run([
    APKSIGNER, "sign", "--ks", "freemytv.keystore", "--ks-pass", "pass:freemytv",
    "--key-pass", "pass:freemytv", "--out", "FreeMyTV.apk", "out/aligned.apk"
], check=True)

print("SUCESSO: FreeMyTV.apk gerado com assets corrigidos!")

