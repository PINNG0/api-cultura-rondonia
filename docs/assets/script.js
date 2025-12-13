async function copiar(caminho, btn) {
  const urlCompleta = new URL(caminho, window.location.href).href;
  try {
    await navigator.clipboard.writeText(urlCompleta);
    btn.classList.add("copied");
    btn.innerHTML = '<i class="fa-solid fa-check" style="color: #4CAF50;"></i>';
    setTimeout(() => {
      btn.classList.remove("copied");
      btn.innerHTML = '<i class="fa-solid fa-copy"></i>';
    }, 1200);
  } catch (err) {
    console.error(err);
  }
}

function filtrar() {
  const termo = document.getElementById("busca").value.toLowerCase();
  const listas = document.querySelectorAll(".card ul");

  listas.forEach(ul => {
    const itens = ul.querySelectorAll("li");
    let temItemVisivel = false;

    itens.forEach(li => {
      const texto = li.innerText.toLowerCase();
      if (texto.includes(termo)) {
        li.style.display = ""; 
        temItemVisivel = true;
      } else {
        li.style.display = "none";
      }
    });

    const card = ul.parentElement;
    if (card) {
      card.style.display = temItemVisivel ? "" : "none";
    }
  });
}