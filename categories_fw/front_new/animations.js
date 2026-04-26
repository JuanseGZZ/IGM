const Animations = {
  _toastEl: null,
  _toastInstance: null,

  init() {
    this._toastEl = document.getElementById('app-toast');
    this._toastInstance = bootstrap.Toast.getOrCreateInstance(this._toastEl, { delay: 3000 });
  },

  toast(msg, type = 'success') {
    const icons = { success: 'bi-check-circle-fill text-success', warning: 'bi-exclamation-triangle-fill text-warning', danger: 'bi-x-circle-fill text-danger', info: 'bi-info-circle-fill text-info' };
    document.getElementById('toast-icon').className = `bi ${icons[type] || icons.info} me-2`;
    document.getElementById('toast-body').textContent = msg;
    this._toastInstance.show();
  },

  spinner(show) {
    document.getElementById('global-spinner').classList.toggle('d-none', !show);
  },

  highlight(el) {
    el.classList.add('impact-flash');
    el.addEventListener('animationend', () => el.classList.remove('impact-flash'), { once: true });
  },

  fadeIn(el) {
    el.classList.remove('fade-in');
    void el.offsetWidth;
    el.classList.add('fade-in');
  },
};
