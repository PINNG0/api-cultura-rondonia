/*
    Script principal do site.

    Responsável por:
    - Busca instantânea
    - Filtragem de cards
    - Interações leves de UX
*/

/* --------------------------- */
/* Busca instantânea           */
/* --------------------------- */

document.addEventListener("input", () => {
    const termo = document.getElementById("busca").value.toLowerCase();
    const cards = document.querySelectorAll(".event-card");

    cards.forEach(card => {
        const texto = card.innerText.toLowerCase();

        // Exibe ou oculta o card conforme o termo digitado
        card.style.display = texto.includes(termo) ? "block" : "none";
    });
});
