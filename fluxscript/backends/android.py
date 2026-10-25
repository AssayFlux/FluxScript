"""Generate a multi-page native Android Kotlin/Gradle source starter."""
from html import escape as xml_escape
from pathlib import Path
from ..models import AppSpec


def _kotlin(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("\n", "\\n").replace("\r", "\\r")


def _page_function(page, index: int) -> str:
    body = []
    for element in page.elements:
        text = _kotlin(element.text)
        if element.kind in {"text", "heading"}:
            size = "24f" if element.kind == "heading" else "16f"
            body.append(f'''        content.addView(TextView(this).apply {{ text = "{text}"; textSize = {size}; setPadding(0, 12, 0, 12) }})''')
        elif element.kind == "button":
            action = _kotlin(element.action or "")
            body.append(f'''        content.addView(Button(this).apply {{ text = "{text}"; setOnClickListener {{ Toast.makeText(this@MainActivity, "Action requested: {action}", Toast.LENGTH_SHORT).show() }} }})''')
        elif element.kind == "input":
            name = _kotlin(element.name or "field")
            input_type = element.attributes.get("input_type", "text")
            body.append(f'''        content.addView(EditText(this).apply {{ hint = "{text}"; tag = "{name}"; contentDescription = "{text}" }})''')
    if not body:
        body.append('        content.addView(TextView(this).apply { text = "No controls on this page." })')
    return f'''    private fun renderPage{index}() {{
        content.removeAllViews()
{chr(10).join(body)}
    }}'''


def generate_android(spec: AppSpec, out: Path) -> list[Path]:
    issues = spec.validate()
    if issues: raise ValueError("Invalid application: " + "; ".join(issues))
    package = "dev.fluxscript.generated"
    app_name = _kotlin(spec.name)
    functions = [_page_function(page, i) for i, page in enumerate(spec.pages)]
    tabs = []
    for index, page in enumerate(spec.pages):
        title = _kotlin(page.title or page.path)
        tabs.append(f'''        tabBar.addView(Button(this).apply {{ text = "{title}"; setOnClickListener {{ renderPage{index}() }} }})''')
    activity = f'''package {package}

import android.app.Activity
import android.os.Bundle
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

class MainActivity : Activity() {{
    private lateinit var content: LinearLayout

    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        title = "{app_name}"
        val root = LinearLayout(this).apply {{
            orientation = LinearLayout.VERTICAL
            setPadding(20, 20, 20, 20)
            layoutParams = ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
        }}
        val tabScroll = HorizontalScrollView(this)
        val tabBar = LinearLayout(this).apply {{ orientation = LinearLayout.HORIZONTAL }}
        tabScroll.addView(tabBar)
        root.addView(tabScroll)
        val scroll = ScrollView(this)
        content = LinearLayout(this).apply {{ orientation = LinearLayout.VERTICAL }}
        scroll.addView(content)
        root.addView(scroll, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
{chr(10).join(tabs)}
        setContentView(root)
        renderPage0()
    }}

{chr(10).join(functions)}
}}
'''
    gradle = '''plugins {
    id("com.android.application") version "8.7.3"
    id("org.jetbrains.kotlin.android") version "2.0.21"
}

android {
    namespace = "dev.fluxscript.generated"
    compileSdk = 35
    defaultConfig {
        applicationId = "dev.fluxscript.generated"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }
}
'''
    settings = '''pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement { repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS); repositories { google(); mavenCentral() } }
rootProject.name = "FluxScriptGeneratedApp"
include(":app")
'''
    manifest = f'''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application android:label="{xml_escape(spec.name, quote=True)}" android:theme="@android:style/Theme.Material.Light.NoActionBar" android:usesCleartextTraffic="false">
        <activity android:name="dev.fluxscript.generated.MainActivity" android:exported="true">
            <intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter>
        </activity>
    </application>
</manifest>
'''
    files = {
        "settings.gradle.kts": settings,
        "build.gradle.kts": 'plugins { id("com.android.application") version "8.7.3" apply false; id("org.jetbrains.kotlin.android") version "2.0.21" apply false }\n',
        "app/build.gradle.kts": gradle,
        "app/src/main/AndroidManifest.xml": manifest,
        "app/src/main/java/dev/fluxscript/generated/MainActivity.kt": activity,
        "README.md": "# Android project generated by FluxScript\n\nThis source starter includes a native Kotlin activity and a tab for every declared page. Buttons emit an action-request toast; implement and test your real application behavior before release. Open in Android Studio with a compatible JDK, Android SDK and Gradle/Android Gradle Plugin. The generator does not sign or package an APK.\n",
    }
    result = []
    for name, content in files.items():
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        result.append(path)
    return result
