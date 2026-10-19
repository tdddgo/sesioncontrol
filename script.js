// Menú móvil
const burger = document.querySelector('.burger');
const nav = document.querySelector('.main-nav');
burger?.addEventListener('click', () => {
  const open = nav.classList.toggle('open');
  burger.setAttribute('aria-expanded', open);
});

// Fecha actual en español en la cabecera
const dateEl = document.getElementById('fecha');
if (dateEl) {
  const f = new Date().toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const [dia, ...resto] = f.split(',');
  dateEl.innerHTML = `<b>${dia.charAt(0).toUpperCase() + dia.slice(1)}</b>${resto.join(',')}`;
}
