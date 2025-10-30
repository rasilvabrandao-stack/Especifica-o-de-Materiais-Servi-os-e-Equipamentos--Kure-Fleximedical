document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('pedidoForm');
  const mensagem = document.getElementById('mensagem');
  const btnEnviar = document.getElementById('btnEnviar');

  // 🔗 URL do Google Apps Script publicada como Web App
  const WEB_APP_URL = 'https://script.google.com/macros/s/AKfycbzTlQpsLZxemQN0WwNJOHiLaTPsWouD8YkFK9NN17oXTHGTrQzyndlML_CPP8rl7W34zA/exec';

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Estado inicial do botão e mensagem
    btnEnviar.disabled = true;
    btnEnviar.textContent = 'Enviando...';
    mensagem.textContent = '';
    mensagem.style.color = '';

    // Captura os dados do formulário
    const dados = {
      emailCliente: form.emailCliente.value.trim(),
      empresa: form.empresa.value.trim(),
      requisitante: form.requisitante.value.trim(),
      projeto: form.projeto.value.trim(),
      centroCusto: form.centroCusto.value.trim(),
      itens: form.itens.value.trim(),
      quantidade: form.quantidade.value.trim(),
      observacoes: form.observacoes.value.trim(),
      dataPrevista: form.dataPrevista.value
    };

    // ⚠️ Validação dos campos obrigatórios
    const camposObrigatorios = ['emailCliente', 'empresa', 'requisitante', 'projeto', 'itens', 'quantidade', 'dataPrevista'];
    for (const campo of camposObrigatorios) {
      if (!dados[campo]) {
        mensagem.textContent = '⚠️ Por favor, preencha todos os campos obrigatórios!';
        mensagem.style.color = 'orange';
        btnEnviar.disabled = false;
        btnEnviar.textContent = 'Enviar Pedido';
        return;
      }
    }

    try {
      // Envia os dados para o Apps Script
      const response = await fetch(WEB_APP_URL, {
        method: 'POST',
        mode: 'cors', // CORS habilitado para receber resposta JSON
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(dados)
      });

      // Verifica se a resposta do servidor é válida
      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`);
      }

      // Lê o JSON retornado pelo Apps Script
      const result = await response.json();

      if (result.sucesso) {
        mensagem.textContent = '✅ Pedido enviado com sucesso!';
        mensagem.style.color = 'green';
        form.reset();
      } else {
        mensagem.textContent = `❌ Erro ao enviar pedido: ${result.erro || result.message || 'Erro desconhecido'}`;
        mensagem.style.color = 'red';
        console.error('Erro retornado pelo servidor:', result);
      }

    } catch (error) {
      // Captura erros de rede, CORS ou problemas no servidor
      mensagem.textContent = '❌ Falha na conexão. Verifique sua internet ou tente novamente.';
      mensagem.style.color = 'red';
      console.error('Erro de conexão ou servidor:', error);
    }

    // Restaura o estado do botão
    btnEnviar.disabled = false;
    btnEnviar.textContent = 'Enviar Pedido';
  });
});
/* Configuração das partículas */
particlesJS("particles", {
  "particles": {
    "number": { "value": 80, "density": { "enable": true, "value_area": 800 } },
    "color": { "value": ["#ffffff", "#8ecbff", "#b18cff"] },
    "shape": { "type": "circle" },
    "opacity": { "value": 0.5 },
    "size": { "value": 3, "random": true },
    "line_linked": { "enable": true, "distance": 150, "color": "#ffffff", "opacity": 0.3, "width": 1 },
    "move": { "enable": true, "speed": 2, "direction": "none", "out_mode": "out" }
  },
  "interactivity": {
    "events": {
      "onhover": { "enable": true, "mode": "grab" },
      "onclick": { "enable": true, "mode": "push" }
    },
    "modes": {
      "grab": { "distance": 200, "line_linked": { "opacity": 0.5 } },
      "push": { "particles_nb": 4 }
    }
  },
  "retina_detect": true
});
