// One listener on the whole document handles buttons that HTMX adds later too // ("event delegation").
document.addEventListener("click", (event) => {
const speakButton = event.target.closest(".speak"); if (speakButton) {
    speak(speakButton.dataset.text);
return; }
const micButton = event.target.closest(".mic"); if (micButton) {
    listen(micButton);
  }
});
function speak(text) {
if (!("speechSynthesis" in window)) return; window.speechSynthesis.cancel();
const utterance = new SpeechSynthesisUtterance(text); utterance.lang = "de-DE";
utterance.rate = 0.9; window.speechSynthesis.speak(utterance);
}
function listen(button) {
const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition; if (!Recognition) {
    alert("Spracheingabe wird in diesem Browser nicht unterstützt.");
return; }
const recognition = new Recognition(); recognition.lang = "de-DE"; recognition.interimResults = false; button.disabled = true; recognition.onresult = (event) => {
const input = button.form.querySelector("input[name=message]"); input.value = event.results[0][0].transcript;
input.focus();
};
recognition.onend = () => { button.disabled = false; }; recognition.start();
}