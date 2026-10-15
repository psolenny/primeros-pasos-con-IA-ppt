// Navegación del deck. No sabe nada del contenido: arma el índice desde el DOM,
// pone el logo correcto según el fondo y lee las notas de cada lámina.
var slides = document.querySelectorAll('.slide');
var ov = document.getElementById('ov');
var np = document.getElementById('np');
var logo = document.getElementById('logo');
var i = 0;

(function () {
  var ol = document.getElementById('ovl');
  slides.forEach(function (s, k) {
    var h = s.querySelector('h1, h2');
    var li = document.createElement('li');
    li.innerHTML = '<span class="i">' + (k + 1) + '</span><span>' +
      (h ? h.textContent.replace(/\s+/g, ' ').trim() : '') + '</span>';
    li.addEventListener('click', function () { show(k); toggleOv(false); });
    ol.appendChild(li);
  });
})();

function toggleOv(force) {
  var open = force === undefined ? !ov.classList.contains('on') : force;
  ov.classList.toggle('on', open);
  if (open) ov.querySelectorAll('li').forEach(function (li, k) { li.className = k === i ? 'cur' : ''; });
}

function show(n) {
  i = Math.max(0, Math.min(slides.length - 1, n));
  slides.forEach(function (s, k) { s.classList.toggle('on', k === i); });
  var s = slides[i];
  document.getElementById('bar').style.width = ((i + 1) / slides.length * 100) + '%';
  document.getElementById('num').textContent = (i + 1) + ' / ' + slides.length;
  // Logo a color solo sobre blanco; sobre azul, negro o rosa va la versión blanca.
  var oscura = s.classList.contains('dark') || s.classList.contains('azul') || s.classList.contains('pop');
  logo.src = oscura ? logo.dataset.blanco : logo.dataset.color;
  logo.style.display = s.hasAttribute('data-nologo') ? 'none' : '';
  var c = oscura ? 'rgba(255,255,255,.75)' : '';
  ['num', 'hint', 'home'].forEach(function (id) { document.getElementById(id).style.color = c; });
  var nt = s.querySelector('.notes');
  document.getElementById('npt').textContent = nt ? nt.textContent.trim() : '—';
  if (location.hash !== '#' + (i + 1)) history.replaceState(null, '', '#' + (i + 1));
}

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') { toggleOv(false); np.classList.remove('on'); return; }
  if (e.key === 'o' || e.key === 'O') { e.preventDefault(); toggleOv(); return; }
  if (e.key === 'n' || e.key === 'N') { e.preventDefault(); np.classList.toggle('on'); return; }
  if (ov.classList.contains('on')) return;
  if (['ArrowRight', ' ', 'PageDown', 'ArrowDown'].indexOf(e.key) > -1) { e.preventDefault(); show(i + 1); }
  if (['ArrowLeft', 'PageUp', 'ArrowUp'].indexOf(e.key) > -1) { e.preventDefault(); show(i - 1); }
  if (e.key === 'Home') { e.preventDefault(); show(0); }
  if (e.key === 'End') { e.preventDefault(); show(slides.length - 1); }
  if (e.key === 'f' || e.key === 'F') {
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen();
  }
});

document.addEventListener('click', function (e) {
  if (e.target.closest('a') || e.target.closest('#ov') || e.target.closest('#np')) return;
  show(e.clientX < window.innerWidth * 0.25 ? i - 1 : i + 1);
});

var x0 = null;
document.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
document.addEventListener('touchend', function (e) {
  if (x0 === null) return;
  var dx = e.changedTouches[0].clientX - x0;
  if (Math.abs(dx) > 50) show(dx < 0 ? i + 1 : i - 1);
  x0 = null;
});

show(parseInt((location.hash || '#1').slice(1), 10) - 1 || 0);
