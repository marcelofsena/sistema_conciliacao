/* ============================================================
   ERP Retaguarda — app.js
   ============================================================ */

/* ---- Highlights na sidebar (página ativa) ---- */
(function markActive() {
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar__link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && path.startsWith(href)) {
      link.classList.add('active');
    } else if (href === '/' && path === '/') {
      link.classList.add('active');
    }
  });
})();

/* ---- Auto-dismiss de alertas ---- */
document.querySelectorAll('.alert[data-auto-dismiss]').forEach(el => {
  const ms = parseInt(el.dataset.autoDismiss) || 5000;
  setTimeout(() => {
    el.style.transition = 'opacity .4s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  }, ms);
});

/* ---- File drop zone ---- */
document.querySelectorAll('.file-drop').forEach(zone => {
  const input = zone.querySelector('.file-drop__input');
  const title = zone.querySelector('.file-drop__title');

  zone.addEventListener('click', () => input && input.click());

  if (input) {
    input.addEventListener('change', () => {
      if (input.files.length > 0) {
        if (title) title.textContent = input.files[0].name;
        zone.classList.add('file-selected');
      }
    });
  }

  ['dragover', 'dragenter'].forEach(evt => {
    zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.add('drag-over'); });
  });
  ['dragleave', 'drop'].forEach(evt => {
    zone.addEventListener(evt, () => zone.classList.remove('drag-over'));
  });
  zone.addEventListener('drop', e => {
    e.preventDefault();
    if (input && e.dataTransfer.files.length > 0) {
      input.files = e.dataTransfer.files;
      if (title) title.textContent = e.dataTransfer.files[0].name;
    }
  });
});

/* ---- Navegação por abertura de caixa ---- */
function mudarAbertura(passo) {
  const select = document.getElementById('select_abertura');
  if (!select) return;
  const current = select.selectedIndex;
  const max = select.options.length - 1;
  const inicial = current === 0 && passo > 0 ? 1 : current + passo;
  if (inicial >= 1 && inicial <= max) {
    select.selectedIndex = inicial;
    const form = document.getElementById('form_conferencia');
    if (form) form.submit();
  }
}

/* ---- Confirmar ação destrutiva ---- */
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', e => {
    const msg = el.dataset.confirm || 'Confirmar esta ação?';
    if (!confirm(msg)) e.preventDefault();
  });
});

/* ---- Loading state em botão de submit ---- */
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', () => {
    const btn = form.querySelector('[type="submit"]');
    if (btn && !btn.dataset.noLoading) {
      btn.disabled = true;
      const original = btn.innerHTML;
      btn.innerHTML = '<span class="spinner"></span> Processando...';
      // Re-enable após 30s (fallback)
      setTimeout(() => { btn.disabled = false; btn.innerHTML = original; }, 30000);
    }
  });
});

/* ---- Formatação de valor monetário em input ---- */
document.querySelectorAll('.input-money').forEach(input => {
  input.addEventListener('blur', () => {
    const val = parseFloat(input.value.replace(',', '.'));
    if (!isNaN(val)) input.value = val.toFixed(2).replace('.', ',');
  });
});

/* ---- Trocar loja ---- */
function trocarLoja(lojaId) {
  const currentPath = window.location.pathname;
  const url = `/trocar-loja/?id=${lojaId}&next=${encodeURIComponent(currentPath)}`;
  window.location.href = url;
}

/* ---- Preservar posição do scroll da sidebar ---- */
(function preserveSidebarScroll() {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;

  // Restaurar scroll ao carregar a página
  const savedScroll = sessionStorage.getItem('sidebar-scroll-position');
  if (savedScroll) {
    sidebar.scrollTop = parseInt(savedScroll, 10);
    sessionStorage.removeItem('sidebar-scroll-position');
  }

  // Salvar scroll ao clicar em links
  document.querySelectorAll('.sidebar__link').forEach(link => {
    link.addEventListener('click', () => {
      sessionStorage.setItem('sidebar-scroll-position', sidebar.scrollTop);
    });
  });
})();
