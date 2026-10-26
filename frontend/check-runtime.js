const fs = require('fs');
const vm = require('vm');

function makeElement(id) {
  return {
    id,
    value: '',
    textContent: '',
    disabled: false,
    hidden: false,
    checked: false,
    className: '',
    children: [],
    style: {},
    dataset: {},
    attributes: {},
    listeners: {},
    classList: { add() {}, remove() {}, toggle() { return false; } },
    appendChild(child) { this.children.push(child); return child; },
    append() { for (const child of arguments) this.children.push(child); },
    replaceChildren(...children) { this.children = children; },
    setAttribute(name, value) { this.attributes[name] = value; },
    removeAttribute(name) { delete this.attributes[name]; },
    addEventListener(type, handler) { this.listeners[type] = handler; },
    dispatchEvent(evt) { if (this.listeners[evt.type]) this.listeners[evt.type](evt); },
    querySelector() { return null; },
    focus() {},
    remove() {},
    scrollTop: 0,
    split: undefined,
    toLocaleString() { return ''; }
  };
}

const ids = [
  'status','sidebar','mobileMenuButton','currentPageName','globalAnnouncement',
  'uploadForm','fileInput','uploadButton','uploadMessage','selectedFiles','dropzone','uploadedDocuments','uploadedFileCount','documentStatusPanel','indexingStatus','documentStatusMessage',
  'chatForm','questionInput','sendButton','messages','clearButton','welcomeMessage','chatSources','chatSourceList',
  'searchForm','searchQuery','searchTopK','searchButton','searchMessage','searchResults',
  'generationForm','generationPrompt','generationLanguage','generationTone','generationLength','generationComplexity','generationFormat','generateButton','generationMessage','generationResultSection','generationPlaceholder','generationResult','generationModel','generationOutputInfo',
  'questionForm','questionSource','questionType','questionCount','questionDifficulty','questionLanguage','includeAnswers','includeTopics','questionGenerateButton','questionMessage','questionResult','questionOutputInfo',
  'imageForm','imageMessage','imageGenerateButton','imageResult','copyGenerationButton','copyQuestionsButton'
];

const map = Object.fromEntries(ids.map((id) => [id, makeElement(id)]));
map.fileInput.files = [];
map.imageForm.querySelector = () => ({ value: 'test prompt', trim: () => 'test prompt' });

const document = {
  getElementById: (id) => map[id] || null,
  querySelectorAll: () => [],
  querySelector: () => null,
  createElement: (tag) => makeElement(tag)
};

const windowObj = {
  setInterval: () => 0,
  fetch: async () => ({ ok: true, text: async () => JSON.stringify({}) })
};

const context = {
  console,
  document,
  window: windowObj,
  fetch: windowObj.fetch,
  FormData: class {},
  navigator: { clipboard: { writeText: async () => {} } },
  Event: function Event(type) { this.type = type; }
};
context.globalThis = context;

vm.runInNewContext(fs.readFileSync('js/app.js', 'utf8'), context, { filename: 'app.js' });
console.log('Runtime evaluation OK');
