(function () {
    "use strict";

    const queueBody = document.getElementById("queue-body");

    if (!queueBody) {
        return;
    }

    function escapeHtml(value) {
        const div = document.createElement("div");
        div.textContent = value ?? "";
        return div.innerHTML;
    }

    function priorityClass(priority) {
        return priority === "Preferencial"
            ? "badge-preferencial"
            : "badge-normal";
    }

    function statusClass(status) {
        return status
            .toLowerCase()
            .replaceAll(" ", "-")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");
    }

    function renderQueue(items) {
        if (!items.length) {
            queueBody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty">
                        A fila está vazia.
                    </td>
                </tr>
            `;

            return;
        }

        let position = 0;

        queueBody.innerHTML = items.map((item) => {
            if (item.status === "Aguardando") {
                position++;
            }

            const posicao =
                item.status === "Aguardando"
                    ? position
                    : "—";

            const telefone =
                item.telefone || "—";

            const action =
                item.status === "Aguardando"
                    ? `
                        <form
                            action="/atendimento/${item.id}/cancelar"
                            method="POST"
                            onsubmit="return confirm('Cancelar este cliente?');"
                        >
                            <button
                                class="btn btn-small btn-danger"
                                type="submit"
                            >
                                Cancelar
                            </button>
                        </form>
                    `
                    : "";

            return `
                <tr>
                    <td>${posicao}</td>

                    <td>
                        <strong>
                            ${escapeHtml(item.nome)}
                        </strong>
                    </td>

                    <td>
                        ${escapeHtml(telefone)}
                    </td>

                    <td>
                        <span class="badge ${priorityClass(item.prioridade)}">
                            ${escapeHtml(item.prioridade)}
                        </span>
                    </td>

                    <td>
                        ${escapeHtml(item.criado_em)}
                    </td>

                    <td>
                        <span class="status status-${statusClass(item.status)}">
                            ${escapeHtml(item.status)}
                        </span>
                    </td>

                    <td>
                        ${action}
                    </td>
                </tr>
            `;
        }).join("");
    }

    async function updateQueue() {
        try {
            const response = await fetch("/api/fila", {
                headers: {
                    "Accept": "application/json"
                },
                cache: "no-store"
            });

            if (!response.ok) {
                return;
            }

            const items = await response.json();

            renderQueue(items);
        } catch (error) {
            console.warn(
                "Não foi possível atualizar a fila:",
                error
            );
        }
    }

    // Atualiza a cada 5 segundos.
    setInterval(updateQueue, 5000);
})();
