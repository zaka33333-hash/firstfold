/* Requests open through GitHub now; replace with hosted checkout URLs when useful. */
const checkoutConfig = {
  fixMap: "https://github.com/zaka33333-hash/firstfold/issues/new?template=audit-request.yml",
  fixSprint: "https://github.com/zaka33333-hash/firstfold/issues/new?template=audit-request.yml"
};

const checkoutStatus = document.querySelector("#checkout-status");

document.querySelectorAll(".checkout-link").forEach((link) => {
  link.addEventListener("click", (event) => {
    const checkoutUrl = checkoutConfig[link.dataset.checkout];
    const isLiveUrl = typeof checkoutUrl === "string" && /^https?:\/\//i.test(checkoutUrl);

    if (!isLiveUrl) {
      event.preventDefault();
      checkoutStatus.hidden = false;
      checkoutStatus.textContent = "Requests are temporarily closed. Please check back shortly.";
      checkoutStatus.focus?.();
      checkoutStatus.scrollIntoView({ behavior: "smooth", block: "nearest" });
      return;
    }

    link.href = checkoutUrl;
  });
});

const sampleBrowser = document.querySelector("[data-sample-browser]");
const annotationTitle = document.querySelector("[data-annotation-title]");
const annotationCopy = document.querySelector("[data-annotation-copy]");
const annotationTwoTitle = document.querySelector("[data-annotation-two-title]");
const annotationTwoCopy = document.querySelector("[data-annotation-two-copy]");

const annotations = {
  before: ["Vague promise", "Could apply to almost anything.", "Generic CTA", "No reason to click now."],
  after: ["Specific audience", "The right visitor knows it is for them.", "Clear next step", "The button makes the value of clicking concrete."]
};

document.querySelectorAll(".view-toggle").forEach((button) => {
  button.addEventListener("click", () => {
    const view = button.dataset.view;
    sampleBrowser.classList.toggle("after", view === "after");
    sampleBrowser.classList.toggle("before", view === "before");
    document.querySelectorAll(".view-toggle").forEach((toggle) => {
      const isSelected = toggle === button;
      toggle.classList.toggle("is-active", isSelected);
      toggle.setAttribute("aria-pressed", String(isSelected));
    });
    [annotationTitle.textContent, annotationCopy.textContent, annotationTwoTitle.textContent, annotationTwoCopy.textContent] = annotations[view];
  });
});
