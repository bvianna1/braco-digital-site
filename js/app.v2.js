(() => {
  'use strict';

  // GA4 — inicialização (movida do <head> para arquivo externo, ver Tarefa 1.4)
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', 'G-P51CNDWHR2');

  // Rastreio de clique em links do WhatsApp (GA4)
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('a[href*="wa.me"]').forEach(function (link) {
      link.addEventListener('click', function () {
        const section = link.closest('section') || link.closest('footer') || link.closest('main');
        gtag('event', 'whatsapp_click', { location: section ? section.id || section.tagName.toLowerCase() : 'unknown' });
      });
    });
  });

  const $ = (selector) => document.querySelector(selector);

  // Menu mobile (só existe na home)
  const menuButton = $('.hamb');
  if (menuButton) {
    menuButton.addEventListener('click', () => {
      const open = document.body.classList.toggle('menu-open');
      menuButton.setAttribute('aria-expanded', String(open));
    });
    document.querySelectorAll('.menu a').forEach((link) => link.addEventListener('click', () => {
      document.body.classList.remove('menu-open');
      menuButton.setAttribute('aria-expanded', 'false');
    }));
  }

  const anoEl = $('#ano');
  if (anoEl) anoEl.textContent = new Date().getFullYear();

  // Calculadora (só existe na home)
  const calcInputs = {
    pessoas: $('#pessoas'),
    custoMensal: $('#custo-mensal'),
    horasSemana: $('#horas-semana'),
  };
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

  // Tarefa 4.1 — link pré-preenchido para o WhatsApp
  const waBase = 'https://wa.me/5521988738405';
  const buildWaLink = () => {
    const s = calculatorState;
    let msg = 'Olá, Bruno. Vi o site da Braço Digital e quero analisar um processo da minha operação.';
    if (s.custoAno > 0) {
      msg += ` Pela calculadora, estimei ${numberBR.format(s.horasAno)} h/ano e ${brl.format(s.custoAno)} por ano em tarefa repetitiva (${s.pessoas} pessoa(s), ${s.horasSemana} h/semana).`;
    }
    return `${waBase}?text=${encodeURIComponent(msg)}`;
  };
  const refreshWaLinks = () => document.querySelectorAll('a[href*="wa.me"]').forEach((a) => { a.href = buildWaLink(); });
  refreshWaLinks();

  if (calcInputs.pessoas && calcInputs.custoMensal && calcInputs.horasSemana) {
    const updateCalculator = () => {
      const values = Object.fromEntries(Object.entries(calcInputs).map(([key, input]) => [key, parseDecimal(input.value)]));
      calculatorState = { ...values, ...calculate(values) };
      const horasAno = $('#horas-ano');
      const custoAno = $('#custo-ano');
      if (horasAno) horasAno.textContent = `${numberBR.format(calculatorState.horasAno)} h`;
      if (custoAno) custoAno.textContent = brl.format(calculatorState.custoAno);
      refreshWaLinks();
      try { sessionStorage.setItem(storageKey, JSON.stringify(values)); } catch (_) { /* armazenamento pode estar indisponível */ }
    };
    try {
      const saved = JSON.parse(sessionStorage.getItem(storageKey));
      if (saved && typeof saved === 'object') Object.entries(calcInputs).forEach(([key, input]) => { if (saved[key] !== undefined) input.value = saved[key]; });
    } catch (_) { /* mantém valores padrão */ }
    Object.values(calcInputs).forEach((input) => input.addEventListener('input', updateCalculator));
    updateCalculator();
  }

  // Formulário de diagnóstico (só existe na home)
  const form = $('#diagnostico-form');
  if (form) {
    const status = $('#form-status');
    const button = form.querySelector('button[type="submit"]');
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      if (status) status.textContent = '';
      if (button) button.disabled = true;
      if (button) button.textContent = 'Enviando…';
      const data = Object.fromEntries(new FormData(form).entries());
      data.calculadora = calculatorState;
      try {
        const response = await fetch('/api/diagnostico', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(data) });
        const result = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(result.error || 'Não foi possível enviar agora. Tente novamente.');
        form.hidden = true;
        const success = $('#form-success');
        if (success) { success.hidden = false; success.focus(); }
        try { window.dataLayer?.push({ event: 'diagnostico_enviado' }); } catch (_) { /* analytics nunca bloqueia o envio */ }
      } catch (error) {
        if (status) status.textContent = error.message || 'Não foi possível enviar agora. Tente novamente.';
        if (button) { button.disabled = false; button.textContent = 'Enviar para análise'; }
      }
    });
  }
})();
