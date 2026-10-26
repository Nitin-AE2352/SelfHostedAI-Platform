
(() => {
  "use strict";

  // FastAPI backend ka address
  const API_BASE = "http://127.0.0.1:8000";
  const $ = (id) => document.getElementById(id);

  // DOM elements
  const status = $("status");
  const sidebar = $("sidebar");
  const mobileMenuButton = $("mobileMenuButton");
  const currentPageName = $("currentPageName");
  const globalAnnouncement = $("globalAnnouncement");

  // Upload controls
  const uploadForm = $("uploadForm");
  const fileInput = $("fileInput");
  const uploadButton = $("uploadButton");
  const uploadMessage = $("uploadMessage");
  const selectedFiles = $("selectedFiles");
  const dropzone = $("dropzone");
  const uploadedDocuments = $("uploadedDocuments");
  const uploadedFileCount = $("uploadedFileCount");
  const documentStatusPanel = $("documentStatusPanel");
  const indexingStatus = $("indexingStatus");
  const documentStatusMessage = $("documentStatusMessage");

  // Chat controls
  const chatForm = $("chatForm");
  const questionInput = $("questionInput");
  const sendButton = $("sendButton");
  const messages = $("messages");
  const clearButton = $("clearButton");
  const welcomeMessage = $("welcomeMessage");
  const chatSources = $("chatSources");
  const chatSourceList = $("chatSourceList");

  // Semantic search controls
  const searchForm = $("searchForm");
  const searchQuery = $("searchQuery");
  const searchTopK = $("searchTopK");
  const searchButton = $("searchButton");
  const searchMessage = $("searchMessage");
  const searchResults = $("searchResults");

  // Text generation controls
  const generationForm = $("generationForm");
  const generationPrompt = $("generationPrompt");
  const generationLanguage = $("generationLanguage");
  const generationTone = $("generationTone");
  const generationLength = $("generationLength");
  const generationComplexity = $("generationComplexity");
  const generationFormat = $("generationFormat");
  const generateButton = $("generateButton");
  const generationMessage = $("generationMessage");
  const generationResultSection = $("generationResultSection");
  const generationPlaceholder = $("generationPlaceholder");
  const generationResult = $("generationResult");
  const generationModel = $("generationModel");
  const generationOutputInfo = $("generationOutputInfo");

  // Question generator controls
  const questionForm = $("questionForm");
  const questionSource = $("questionSource");
  const questionType = $("questionType");
  const questionCount = $("questionCount");
  const questionDifficulty = $("questionDifficulty");
  const questionLanguage = $("questionLanguage");
  const includeAnswers = $("includeAnswers");
  const includeTopics = $("includeTopics");
  const questionGenerateButton = $("questionGenerateButton");
  const questionMessage = $("questionMessage");
  const questionResult = $("questionResult");
  const questionOutputInfo = $("questionOutputInfo");

  // Image generation controls
  const imageForm = $("imageForm");
  const imageMessage = $("imageMessage");
  const imageGenerateButton = $("imageGenerateButton");
  const imageResult = $("imageResult");

  // Current browser session ke uploaded documents
  const uploadedFileNames = new Set();

  // --------------------------------------------------
  // 1. Common message helpers
  // --------------------------------------------------

  function showMessage(element, message, isError = false) {
    if (!element) return;

    element.textContent = message || "";
    element.classList.toggle("error", Boolean(isError));
    element.style.color = isError ? "#dc2626" : "";
    element.setAttribute("role", isError ? "alert" : "status");
  }

  function announce(message, isError = false) {
    showMessage(globalAnnouncement, message, isError);
  }

  function setButtonLoading(button, loading, loadingText, normalText) {
    if (!button) return;

    button.disabled = loading;
    button.textContent = loading ? loadingText : normalText;
  }

  function getErrorMessage(error) {
    if (error instanceof TypeError) {
      return (
        "Backend se connection nahi ho raha. " +
        "Check karo FastAPI http://127.0.0.1:8000 par running hai."
      );
    }

    return error instanceof Error
      ? error.message
      : "Unexpected error occurred.";
  }

  // --------------------------------------------------
  // 2. API request helper
  // --------------------------------------------------

  async function apiFetch(path, options = {}) {
    let response;

    try {
      response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
          ...(options.headers || {})
        }
      });
    } catch (error) {
      if (error instanceof TypeError) {
        throw new Error(
          "Backend se connection nahi ho raha. " +
          "FastAPI server aur CORS configuration check karo."
        );
      }

      throw error;
    }

    const rawText = await response.text();
    let data = {};

    try {
      data = rawText ? JSON.parse(rawText) : {};
    } catch {
      data = { detail: rawText };
    }

    if (!response.ok) {
      const detail =
        data.detail ??
        data.message ??
        data.error ??
        response.statusText ??
        "Request failed.";

      const message =
        typeof detail === "string"
          ? detail
          : JSON.stringify(detail);

      throw new Error(
        `HTTP ${response.status}: ${message}`
      );
    }

    return data;
  }

  // API response se readable text nikalna.
  // Different backend response formats ko handle karta hai.
  function getResponseText(data) {
    if (typeof data === "string") return data;

    const candidates = [
      data?.answer,
      data?.response,
      data?.text,
      data?.content,
      data?.result
    ];

    for (const value of candidates) {
      if (typeof value === "string" && value.trim()) {
        return value;
      }
    }

    return "";
  }

  // --------------------------------------------------
  // 3. Backend health check
  // --------------------------------------------------

  async function checkBackend() {
    if (!status) return;

    status.className = "status-pill checking";
    status.textContent = "Checking backend...";

    try {
      await apiFetch("/health");

      status.className = "status-pill connected";
      status.textContent = "● Backend connected";
    } catch {
      status.className = "status-pill disconnected";
      status.textContent = "● Backend unavailable";
    }
  }

  // --------------------------------------------------
  // 4. Document upload UI
  // --------------------------------------------------

  function updateSelectedFiles(files) {
    const fileList = Array.from(files || []);

    if (selectedFiles) {
      selectedFiles.textContent = fileList.length
        ? `${fileList.length} file(s) selected: ${
            fileList.map((file) => file.name).join(", ")
          }`
        : "No files selected";
    }

    if (fileList.length > 10) {
      showMessage(
        uploadMessage,
        "Maximum 10 files per upload. Select 10 or fewer.",
        true
      );
    } else {
      showMessage(uploadMessage, "");
    }
  }

  function renderUploadedDocuments() {
    if (!uploadedDocuments) return;

    uploadedDocuments.replaceChildren();

    if (uploadedFileNames.size === 0) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "Uploaded documents will appear here.";
      uploadedDocuments.appendChild(empty);
    } else {
      uploadedFileNames.forEach((name) => {
        const item = document.createElement("div");
        item.className = "uploaded-file-item";

        const icon = document.createElement("div");
        icon.className = "uploaded-file-icon";
        icon.textContent = "▤";

        const details = document.createElement("div");
        details.className = "uploaded-file-details";

        const title = document.createElement("div");
        title.className = "uploaded-file-name";
        title.textContent = name;

        const meta = document.createElement("div");
        meta.className = "uploaded-file-meta";
        meta.textContent = "Uploaded in this browser session";

        details.append(title, meta);
        item.append(icon, details);
        uploadedDocuments.appendChild(item);
      });
    }

    if (uploadedFileCount) {
      uploadedFileCount.textContent = String(uploadedFileNames.size);
    }
  }

  function setIndexingStatus(message, isError = false) {
    showMessage(documentStatusMessage, message, isError);

    if (indexingStatus) {
      indexingStatus.textContent = isError
        ? "Needs attention"
        : "Document status";
    }
  }

  fileInput?.addEventListener("change", () => {
    updateSelectedFiles(fileInput.files);
  });

  // Drag-and-drop
  if (dropzone && fileInput) {
    ["dragenter", "dragover"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.add("drag-over");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.remove("drag-over");
      });
    });

    dropzone.addEventListener("drop", (event) => {
      const files = event.dataTransfer?.files;

      if (!files?.length) return;

      try {
        fileInput.files = files;
        updateSelectedFiles(fileInput.files);
      } catch {
        showMessage(
          uploadMessage,
          "Files select karne ke liye Browse button use karo.",
          true
        );
      }
    });
  }

  uploadForm?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const files = Array.from(fileInput?.files || []);

    if (!files.length) {
      showMessage(uploadMessage, "Please select at least one document.", true);
      return;
    }

    if (files.length > 10) {
      showMessage(uploadMessage, "Maximum 10 files per upload.", true);
      return;
    }

    // Current backend ke supported extensions
    const allowedExtension = /\.(pdf|docx|pptx|txt)$/i;
    const invalidFiles = files.filter(
      (file) => !allowedExtension.test(file.name)
    );

    if (invalidFiles.length) {
      showMessage(
        uploadMessage,
        "Unsupported files: " +
          invalidFiles.map((file) => file.name).join(", ") +
          ". Supported formats: PDF, DOCX, PPTX, TXT.",
        true
      );
      return;
    }

    const formData = new FormData();

    files.forEach((file) => {
      formData.append("files", file);
    });

    setButtonLoading(
      uploadButton,
      true,
      "Uploading and indexing...",
      "Upload and index documents"
    );

    if (documentStatusPanel) {
      documentStatusPanel.hidden = false;
    }

    setIndexingStatus(
      "Documents upload ho rahe hain aur searchable text prepare ho raha hai."
    );

    showMessage(uploadMessage, "Uploading documents...");

    try {
      const data = await apiFetch("/api/v1/documents/upload", {
        method: "POST",
        body: formData
      });

      const result =
        data.message ??
        data.detail ??
        "Upload request completed.";

      showMessage(
        uploadMessage,
        typeof result === "string"
          ? result
          : JSON.stringify(result, null, 2)
      );

      // Sirf successful upload ke baad local list update hogi.
      files.forEach((file) => uploadedFileNames.add(file.name));
      renderUploadedDocuments();

      setIndexingStatus(
        "Upload request successful. Documents search karne ke liye ready hone chahiye."
      );

      fileInput.value = "";
      updateSelectedFiles([]);

      announce("Document upload request completed.");
    } catch (error) {
      const message = getErrorMessage(error);

      showMessage(uploadMessage, `Upload failed: ${message}`, true);
      setIndexingStatus(message, true);
    } finally {
      setButtonLoading(
        uploadButton,
        false,
        "Uploading and indexing...",
        "Upload and index documents"
      );
    }
  });

  // --------------------------------------------------
  // 5. RAG chat
  // --------------------------------------------------

  function addChatMessage(text, role = "assistant", model = "") {
    if (!messages) return null;

    welcomeMessage?.remove();

    const card = document.createElement("div");
    card.className = `message-card ${role}`;

    const body = document.createElement("div");
    body.className = "message-text";
    body.textContent = String(text ?? "");

    card.appendChild(body);

    if (model && role === "assistant") {
      const modelInfo = document.createElement("div");
      modelInfo.className = "message-model";
      modelInfo.textContent = `Model: ${model}`;
      card.appendChild(modelInfo);
    }

    messages.appendChild(card);
    messages.scrollTop = messages.scrollHeight;

    return card;
  }

  function getSources(data) {
    const sources = data?.sources ?? data?.source ?? [];

    if (Array.isArray(sources)) {
      return sources.map((source) => {
        if (typeof source === "string") {
          return { label: source, detail: "" };
        }

        if (!source || typeof source !== "object") {
          return { label: String(source), detail: "" };
        }

        const label =
          source.filename ??
          source.file_name ??
          source.source ??
          source.document ??
          source.name ??
          "Source";

        const page = source.page ?? source.page_number;
        const detail =
          page !== undefined && page !== null
            ? `Page ${page}`
            : "";

        return { label: String(label), detail };
      });
    }

    if (typeof sources === "string" && sources.trim()) {
      return sources.split("\n").map((line) => ({
        label: line.trim(),
        detail: ""
      }));
    }

    return [];
  }

  function renderChatSources(sources) {
    if (chatSources) {
      chatSources.hidden = sources.length === 0;
    }

    if (!chatSourceList) return;

    chatSourceList.replaceChildren();

    sources.forEach((source) => {
      const item = document.createElement("div");
      item.className = "chat-source-item";

      const title = document.createElement("b");
      title.textContent = source.label;

      item.appendChild(title);

      if (source.detail) {
        const detail = document.createElement("p");
        detail.textContent = source.detail;
        item.appendChild(detail);
      }

      chatSourceList.appendChild(item);
    });
  }

  chatForm?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const userMessage = questionInput?.value.trim();

    if (!userMessage) {
      questionInput?.focus();
      return;
    }

    addChatMessage(userMessage, "user");
    questionInput.value = "";
    questionInput.disabled = true;

    setButtonLoading(sendButton, true, "…", "↑");

    const loadingMessage = addChatMessage(
      "Searching documents and generating an answer..."
    );

    renderChatSources([]);

    try {
      const data = await apiFetch("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage })
      });

      loadingMessage?.remove();

      const answer = getResponseText(data);

      if (!answer) {
        throw new Error(
          "API ne answer return nahi kiya. /docs mein POST /api/v1/chat check karo."
        );
      }

      addChatMessage(answer, "assistant", data.model || "");

      const sources = getSources(data);
      renderChatSources(sources);
    } catch (error) {
      loadingMessage?.remove();

      addChatMessage(
        `Request failed: ${getErrorMessage(error)}`,
        "assistant"
      );
    } finally {
      questionInput.disabled = false;
      setButtonLoading(sendButton, false, "…", "↑");
      questionInput.focus();
    }
  });

  clearButton?.addEventListener("click", () => {
    if (!messages) return;

    messages.replaceChildren();

    if (welcomeMessage) {
      welcomeMessage.hidden = false;
      messages.appendChild(welcomeMessage);
    } else {
      addChatMessage(
        "Chat cleared. Ask a new question about your uploaded documents."
      );
    }

    renderChatSources([]);
  });

  document.querySelectorAll(".suggestion").forEach((button) => {
    button.addEventListener("click", () => {
      if (!questionInput) return;

      questionInput.value =
        button.dataset.question || button.textContent.trim();

      questionInput.focus();
    });
  });

  // --------------------------------------------------
  // 6. Semantic search
  // --------------------------------------------------

  function renderSearchResults(data) {
    if (!searchResults) return;

    searchResults.replaceChildren();

    let results =
      data.results ??
      data.matches ??
      data.documents ??
      data.sources ??
      [];

    if (!Array.isArray(results)) {
      results = [];
    }

    // Kuch backends ek single result object return kar sakte hain.
    if (results.length === 0 && data.document) {
      results = [data];
    }

    if (results.length === 0) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent =
        "No matching passages returned. Documents upload aur index hue hain ya nahi check karo.";
      searchResults.appendChild(empty);
      return;
    }

    results.forEach((result, index) => {
      const card = document.createElement("article");
      card.className = "search-result-card";

      const title = document.createElement("h4");
      title.textContent =
        result.filename ??
        result.file_name ??
        result.source ??
        result.document ??
        result.name ??
        `Result ${index + 1}`;

      const meta = document.createElement("div");
      meta.className = "search-result-meta";

      const page = result.page ?? result.page_number;
      const score = result.score ?? result.similarity;

      const metaParts = [];

      if (page !== undefined && page !== null) {
        metaParts.push(`Page ${page}`);
      }

      if (typeof score === "number") {
        metaParts.push(`Score: ${score.toFixed(3)}`);
      }

      meta.textContent = metaParts.join(" · ");

      const content = document.createElement("p");
      content.className = "search-result-content";
      content.textContent =
        result.text ??
        result.content ??
        result.chunk ??
        result.page_content ??
        "";

      card.append(title, meta, content);
      searchResults.appendChild(card);
    });
  }

  searchForm?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const query = searchQuery?.value.trim();

    if (!query) {
      showMessage(searchMessage, "Enter a search query first.", true);
      searchQuery?.focus();
      return;
    }

    setButtonLoading(searchButton, true, "Searching...", "Search documents");
    showMessage(searchMessage, "Searching indexed documents...");

    if (searchResults) {
      searchResults.replaceChildren();
    }

    try {
      const data = await apiFetch("/api/v1/documents/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          top_k: Number(searchTopK?.value || 4)
        })
      });

      renderSearchResults(data);
      showMessage(searchMessage, "Search completed.");
    } catch (error) {
      showMessage(
        searchMessage,
        `Search failed: ${getErrorMessage(error)}`,
        true
      );
    } finally {
      setButtonLoading(
        searchButton,
        false,
        "Searching...",
        "Search documents"
      );
    }
  });

  // --------------------------------------------------
  // 7. Copy output helper
  // --------------------------------------------------

  async function copyOutput(text, messageElement) {
    const value = String(text || "").trim();

    if (!value) {
      showMessage(messageElement, "There is no output to copy.", true);
      return;
    }

    try {
      await navigator.clipboard.writeText(value);
      showMessage(messageElement, "Copied to clipboard.");
    } catch {
      // Clipboard API unavailable ho to manual copy ka message.
      showMessage(
        messageElement,
        "Clipboard access unavailable. Output select karke manually copy karo.",
        true
      );
    }
  }

  $("copyGenerationButton")?.addEventListener("click", () => {
    copyOutput(generationResult?.textContent || "", generationMessage);
  });

  $("copyQuestionsButton")?.addEventListener("click", () => {
    copyOutput(questionResult?.textContent || "", questionMessage);
  });

  // --------------------------------------------------
  // 8. Text generation
  // --------------------------------------------------

  generationForm?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const prompt = generationPrompt?.value.trim();

    if (!prompt) {
      showMessage(generationMessage, "Enter a prompt first.", true);
      generationPrompt?.focus();
      return;
    }

    setButtonLoading(
      generateButton,
      true,
      "Generating...",
      "✦ Generate content"
    );

    showMessage(
      generationMessage,
      "Local model content generate kar raha hai. Ismein time lag sakta hai."
    );

    if (generationResultSection) generationResultSection.hidden = true;
    if (generationPlaceholder) generationPlaceholder.hidden = false;

    try {
      const data = await apiFetch("/api/v1/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          language: generationLanguage?.value || "English",
          tone: generationTone?.value || "professional",
          length: generationLength?.value || "medium",
          complexity: generationComplexity?.value || "intermediate",
          output_format: generationFormat?.value || "text"
        })
      });

      const output = getResponseText(data);

      if (!output) {
        throw new Error(
          "Generated text nahi mila. /docs mein POST /api/v1/generate check karo."
        );
      }

      if (generationResult) generationResult.textContent = output;

      if (generationModel) {
        generationModel.textContent = data.model
          ? `Model: ${data.model}`
          : "Local model output";
      }

      if (generationOutputInfo) {
        generationOutputInfo.textContent =
          `${output.length.toLocaleString()} characters`;
      }

      if (generationResultSection) generationResultSection.hidden = false;
      if (generationPlaceholder) generationPlaceholder.hidden = true;

      showMessage(generationMessage, "Content generated successfully.");
    } catch (error) {
      showMessage(
        generationMessage,
        `Generation failed: ${getErrorMessage(error)}`,
        true
      );
    } finally {
      setButtonLoading(
        generateButton,
        false,
        "Generating...",
        "✦ Generate content"
      );
    }
  });

  // --------------------------------------------------
  // 9. Question generation
  // --------------------------------------------------

  questionForm?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const sourceText = questionSource?.value.trim();

    if (!sourceText) {
      showMessage(
        questionMessage,
        "Enter a topic or paste learning content first.",
        true
      );
      questionSource?.focus();
      return;
    }

    setButtonLoading(
      questionGenerateButton,
      true,
      "Generating questions...",
      "Generate questions"
    );

    showMessage(questionMessage, "Generating questions with the local model...");

    if (questionResult) questionResult.textContent = "";

    try {
      const data = await apiFetch("/api/v1/questions/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_text: sourceText,
          question_type: questionType?.value || "MCQ",
          count: Number(questionCount?.value || 5),
          difficulty: questionDifficulty?.value || "Easy",
          language: questionLanguage?.value || "English",
          include_answers: Boolean(includeAnswers?.checked),
          include_topics: Boolean(includeTopics?.checked)
        })
      });

      const output = getResponseText(data);

      if (!output) {
        throw new Error(
          "Questions return nahi hue. /docs mein POST /api/v1/questions/generate check karo."
        );
      }

      if (questionResult) questionResult.textContent = output;

      if (questionOutputInfo) {
        questionOutputInfo.textContent =
          `${output.length.toLocaleString()} characters`;
      }

      showMessage(
        questionMessage,
        `Question set generated${data.model ? ` with ${data.model}` : ""}.`
      );
    } catch (error) {
      showMessage(
        questionMessage,
        `Question generation failed: ${getErrorMessage(error)}`,
        true
      );
    } finally {
      setButtonLoading(
        questionGenerateButton,
        false,
        "Generating questions...",
        "Generate questions"
      );
    }
  });

  // --------------------------------------------------
  // 10. Image generation
  // --------------------------------------------------

  imageForm?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const promptField = imageForm.querySelector(
      '[name="prompt"], #imagePrompt'
    );

    const sizeField = imageForm.querySelector('[name="size"]');
    const styleField = imageForm.querySelector('[name="style"]');
    const kindField = imageForm.querySelector('[name="kind"]');

    const prompt = promptField?.value?.trim();

    if (!prompt || prompt.length < 3) {
      showMessage(
        imageMessage,
        "Please enter an image prompt with at least 3 characters.",
        true
      );
      return;
    }

    // Backend abhi maximum 512 x 512 support karta hai.
    const dimensions = (sizeField?.value || "512x512")
      .split("x")
      .map(Number);

    const width = Math.min(512, Math.max(256, dimensions[0] || 512));
    const height = Math.min(512, Math.max(256, dimensions[1] || 512));

    const style = styleField?.value || "clean";
    const kind = kindField?.value || "image";

    const finalPrompt =
      `${prompt}. Visual type: ${kind}. Art style: ${style}.`;

    if (imageGenerateButton) {
      imageGenerateButton.disabled = true;
      imageGenerateButton.textContent = "Generating image...";
    }

    if (imageResult) {
      imageResult.hidden = true;
      imageResult.replaceChildren();
    }

    showMessage(
      imageMessage,
      "Image model load ho raha hai ya image generate ho rahi hai. CPU par samay lag sakta hai.",
      false
    );

    try {
     const data = await apiFetch("/api/v1/images/generate", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    prompt: finalPrompt,
    width,
    height,
    steps: 15
  })
});

      if (!data.image_base64) {
        throw new Error("Backend response mein generated image nahi mili.");
      }

      const mimeType = data.mime_type || "image/png";
      const imageUrl = `data:${mimeType};base64,${data.image_base64}`;

      const image = document.createElement("img");
      image.src = imageUrl;
      image.alt = prompt;

      const downloadLink = document.createElement("a");
      downloadLink.href = imageUrl;
      downloadLink.download = "generated-image.png";
      downloadLink.textContent = "Download image";
      downloadLink.className = "btn";

      const modelInfo = document.createElement("p");
      modelInfo.textContent = `Model: ${data.model || "Local image model"}`;

      imageResult.replaceChildren(image, modelInfo, downloadLink);
      imageResult.hidden = false;

      showMessage(
        imageMessage,
        "Image successfully generate ho gayi!",
        false
      );
    } catch (error) {
      showMessage(
        imageMessage,
        `Image generation failed: ${error.message}`,
        true
      );
    } finally {
      if (imageGenerateButton) {
        imageGenerateButton.disabled = false;
        imageGenerateButton.textContent = "Generate Image";
        imageGenerateButton.title = "";
      }
    }
  });

  if (imageGenerateButton) {
    imageGenerateButton.disabled = false;
    imageGenerateButton.classList.remove("disabled");
    imageGenerateButton.textContent = "Generate Image";
    imageGenerateButton.title = "Generate an image using the local backend";
  }

  // --------------------------------------------------
  // 11. Sidebar and page navigation
  // --------------------------------------------------

  mobileMenuButton?.addEventListener("click", () => {
    const isOpen = sidebar?.classList.toggle("open") || false;
    mobileMenuButton.setAttribute("aria-expanded", String(isOpen));
  });

  document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", () => {
      document.querySelectorAll(".nav-link").forEach((item) => {
        item.classList.remove("active");
        item.removeAttribute("aria-current");
      });

      link.classList.add("active");
      link.setAttribute("aria-current", "page");

      if (currentPageName) {
        currentPageName.textContent =
          link.dataset.pageName ||
          link.textContent.trim();
      }

      sidebar?.classList.remove("open");
      mobileMenuButton?.setAttribute("aria-expanded", "false");
    });
  });

  // --------------------------------------------------
  // 12. Initial setup
  // --------------------------------------------------

  renderUploadedDocuments();
  updateSelectedFiles([]);
  renderChatSources([]);
  checkBackend();

  // Backend status refresh
  window.setInterval(checkBackend, 30000);
})();
