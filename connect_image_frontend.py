from pathlib import Path

root = Path.cwd()
js_path = root / "frontend" / "js" / "app.js"
html_path = root / "frontend" / "index.html"

if not js_path.is_file() or not html_path.is_file():
    raise SystemExit(
        "Frontend files nahi mile. Expected: frontend/js/app.js and frontend/index.html"
    )

js = js_path.read_text(encoding="utf-8")
html = html_path.read_text(encoding="utf-8")

old_js = '''  // Image generation needs a backend endpoint before it can work.
  $("imageForm")?.addEventListener("submit", (event) => {
    event.preventDefault();
    showMessage($("imageMessage"), "Image generation API abhi backend mein implement nahi hai.", true);
  });'''

new_js = '''  // Connect Image Studio to the existing local FastAPI image endpoint.
  $("imageForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const prompt = $("imagePrompt")?.value.trim();
    const message = $("imageMessage");
    const button = $("imageGenerateButton");
    const preview = $("imagePreview");
    const placeholder = $("imagePreviewPlaceholder");
    const download = $("imageDownloadLink");
    const modelLabel = $("imageModelLabel");

    if (!prompt || prompt.length < 3) {
      showMessage(message, "Image prompt kam se kam 3 characters ka hona chahiye.", true);
      $("imagePrompt")?.focus();
      return;
    }

    const [rawWidth, rawHeight] = ($("imageSize")?.value || "512x512")
      .split("x").map(Number);
    const width = Math.min(512, Math.max(256, rawWidth || 512));
    const height = Math.min(512, Math.max(256, rawHeight || 512));

    const kindLabels = {
      image: "",
      "educational-illustration": "Educational illustration.",
      diagram: "Diagram-style visual with clear, simple elements.",
      "flat-vector": "Flat vector-style artwork."
    };
    const styleLabels = {
      clean: "Clean, minimal composition.",
      flat: "Flat illustration style.",
      realistic: "Realistic visual style.",
      diagram: "Clear diagram style.",
      watercolor: "Watercolor art style."
    };

    const kind = kindLabels[$("imageKind")?.value] || "";
    const style = styleLabels[$("imageStyle")?.value] || "";
    const finalPrompt = [kind, style, prompt].filter(Boolean).join(" ");

    if (button) {
      button.disabled = true;
      button.textContent = "Generating image...";
    }
    showMessage(message, "Local image model image bana raha hai. CPU par ismein kuch samay lag sakta hai.");
    if (download) download.hidden = true;

    try {
      const data = await apiFetch("/api/v1/images/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: finalPrompt,
          width,
          height,
          steps: 15
        })
      });

      if (!data.image_base64) {
        throw new Error("Image API ne image data return nahi kiya.");
      }

      const mimeType = data.mime_type || "image/png";
      const imageUrl = `data:${mimeType};base64,${data.image_base64}`;

      if (preview) {
        preview.src = imageUrl;
        preview.hidden = false;
        preview.style.display = "block";
        preview.style.maxWidth = "100%";
        preview.style.maxHeight = "520px";
        preview.style.objectFit = "contain";
        preview.style.borderRadius = "12px";
      }

      if (placeholder) placeholder.hidden = true;

      if (download) {
        download.href = imageUrl;
        download.download = "generated-image.png";
        download.hidden = false;
      }

      if (modelLabel) {
        modelLabel.textContent = `Local model: ${data.model || "Image model"} · ${width} × ${height}`;
      }

      showMessage(message, "Image generated successfully.");
    } catch (error) {
      showMessage(message, `Image generation failed: ${errorText(error)}`, true);
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = "Generate image";
      }
    }
  });'''

old_button = '<button class="btn disabled full" id="imageGenerateButton" type="button" disabled>Image generation backend not connected</button>'
new_button = '<button class="btn primary full" id="imageGenerateButton" type="submit">Generate image</button>'

old_preview = '<article class="panel image-preview"><div class="placeholder-art">▧</div><h3>Image preview</h3><p>Generated images will appear here once an image worker and API endpoint are integrated.</p><span class="pill-muted">SDXL / FLUX candidates require license and GPU validation</span></article>'
new_preview = '''<article class="panel image-preview">
<div id="imagePreviewPlaceholder"><div class="placeholder-art">▧</div><h3>Image preview</h3><p>Your generated image will appear here.</p></div>
<img id="imagePreview" alt="Generated image preview" hidden>
<p id="imageModelLabel" class="tiny"></p>
<a id="imageDownloadLink" class="btn ghost" href="#" download="generated-image.png" hidden>Download PNG</a>
</article>'''

old_size = '<select id="imageSize"><option value="512x512">512 × 512</option><option value="768x768" selected>768 × 768</option><option value="1024x1024">1024 × 1024</option><option value="1024x768">1024 × 768</option><option value="768x1024">768 × 1024</option></select>'
new_size = '<select id="imageSize"><option value="512x512" selected>512 × 512</option><option value="512x384">512 × 384</option><option value="384x512">384 × 512</option></select>'

old_format = '<select id="imageFormat"><option value="png">PNG</option><option value="jpeg">JPEG</option><option value="webp">WebP</option></select>'
new_format = '<select id="imageFormat"><option value="png">PNG (supported by backend)</option></select>'

replacements = [
    (js, old_js, new_js, "image API handler"),
    (html, old_button, new_button, "image submit button"),
    (html, old_preview, new_preview, "image preview"),
    (html, old_size, new_size, "supported image dimensions"),
    (html, old_format, new_format, "supported image format"),
]

for source, old, new, label in replacements:
    count = source.count(old)
    if count != 1:
        raise SystemExit(
            f"Update rok diya: {label} ka expected exact block ek baar milna chahiye; mila {count}. "
            "Files ko manually change nahi kiya gaya."
        )

js = js.replace(old_js, new_js, 1)
html = html.replace(old_button, new_button, 1)
html = html.replace(old_preview, new_preview, 1)
html = html.replace(old_size, new_size, 1)
html = html.replace(old_format, new_format, 1)

js_backup = js_path.with_suffix(".js.before-image-integration.bak")
html_backup = html_path.with_name("index.html.before-image-integration.bak")

js_backup.write_text(js_path.read_text(encoding="utf-8"), encoding="utf-8")
html_backup.write_text(html_path.read_text(encoding="utf-8"), encoding="utf-8")

js_path.write_text(js, encoding="utf-8")
html_path.write_text(html, encoding="utf-8")

print("Image frontend integration updated.")
print(f"Backup: {js_backup}")
print(f"Backup: {html_backup}")
print("API endpoint: POST /api/v1/images/generate")
print("Response fields used: image_base64, mime_type, model")
