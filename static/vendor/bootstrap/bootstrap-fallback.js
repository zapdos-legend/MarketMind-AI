(function () {
  if (window.bootstrap) return;
  window.bootstrap = {
    Alert: { getOrCreateInstance: function (el) { return { close: function () { el.remove(); } }; } }
  };
  document.addEventListener('click', function (event) {
    var toggler = event.target.closest('[data-bs-toggle="collapse"]');
    if (!toggler) return;
    var target = document.querySelector(toggler.getAttribute('data-bs-target'));
    if (!target) return;
    target.classList.toggle('show');
    toggler.setAttribute('aria-expanded', target.classList.contains('show') ? 'true' : 'false');
  });
})();
