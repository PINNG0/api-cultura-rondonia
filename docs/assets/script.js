function copiar(url, btn) {
  navigator.clipboard.writeText(url);
  btn.classList.add("copied");
  btn.innerHTML = '<i class="fa-solid fa-check"></i>';
  setTimeout(() => {
    btn.classList.remove("copied");
    btn.innerHTML = '<i class="fa-solid fa-copy"></i>';
  }, 1200);
}

function filtrar() {
  const termo = document.getElementById("busca").value.toLowerCase();
  const itens = document.querySelectorAll("li");

  itens.forEach(li => {
    const texto = li.innerText.toLowerCase();
    li.style.display = texto.includes(termo) ? "flex" : "none";
  });
}
