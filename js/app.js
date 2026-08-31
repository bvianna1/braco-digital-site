(() => {
  'use strict';

  // Rastreio de clique em links do WhatsApp (GA4)
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('a[href*="wa.me"]').forEach(function (link) {
      link.addEventListener('click', function () {
        gtag('event', 'click_whatsapp', { link_url: link.href });
      });
    });
  });

  const $ = (selector) => document.querySelector(selector);
  const menuButton = $('.hamb');
  menuButton.addEventListener('click', () => {
    const open = document.body.classList.toggle('menu-open');
    menuButton.setAttribute('aria-expanded', String(open));
  });
  document.querySelectorAll('.menu a').forEach((link) => link.addEventListener('click', () => {
    document.body.classList.remove('menu-open');
    menuButton.setAttribute('aria-expanded', 'false');
  }));
  $('#ano').textContent = new Date().getFullYear();

  const calcInputs = { pessoas: $('#pessoas'), custoMensal: $('#custo-mensal'), horasSemana: $('#horas-semana') };
  const storageKey = 'bracoDigitalCalculadora.v2';
  const parseDecimal = (value) => {
    const clean = String(value ?? '').trim().replace(/\s/g, '').replace(',', '.');
    const number = Number(clean);
    return Number.isFinite(number) && number >= 0 ? number : 0;
  };
  const calculate = ({ pessoas, custoMensal, horasSemana }) => {
    const horasAno = pessoas * horasSemana * 48;
    const custoHora = custoMensal / 160;
    return { horasAno, custoHora, custoAno: horasAno * custoHora };
  };
  const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
  const numberBR = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 });
  let calculatorState = { pessoas: 0, custoMensal: 0, horasSemana: 0, horasAno: 0, custoHora: 0, custoAno: 0 };
  const updateCalculator = () => {
    const values = Object.fromEntries(Object.entries(calcInputs).map(([key, input]) => [key, parseDecimal(input.value)]));
    calculatorState = { ...values, ...calculate(values) };
    $('#horas-ano').textContent = `${numberBR.format(calculatorState.horasAno)} h`;
    $('#custo-ano').textContent = brl.format(calculatorState.custoAno);
    try { sessionStorage.setItem(storageKey, JSON.stringify(values)); } catch (_) { /* armazenamento pode estar indisponível */ }
  };
  try {
    const saved = JSON.parse(sessionStorage.getItem(storageKey));
    if (saved && typeof saved === 'object') Object.entries(calcInputs).forEach(([key, input]) => { if (saved[key] !== undefined) input.value = saved[key]; });
  } catch (_) { /* mantém valores padrão */ }
  Object.values(calcInputs).forEach((input) => input.addEventListener('input', updateCalculator));
  updateCalculator();

  const form = $('#diagnostico-form');
  const status = $('#form-status');
  const button = form.querySelector('button[type="submit"]');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    status.textContent = '';
    if (!form.checkValidity()) { form.reportValidity(); return; }
    button.disabled = true;
    button.textContent = 'Enviando…';
    const data = Object.fromEntries(new FormData(form).entries());
    data.calculadora = calculatorState;
    try {
      const response = await fetch('/api/diagnostico', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(data) });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || 'Não foi possível enviar agora. Tente novamente.');
      form.hidden = true;
      const success = $('#form-success');
      success.hidden = false;
      success.focus();
      try { window.dataLayer?.push({ event: 'diagnostico_enviado' }); } catch (_) { /* analytics nunca bloqueia o envio */ }
    } catch (error) {
      status.textContent = error.message || 'Não foi possível enviar agora. Tente novamente.';
      button.disabled = false;
      button.textContent = 'Enviar para análise';
    }
  });
})();
