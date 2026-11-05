(function () {
  const board = document.querySelector("[data-kanban]");
  if (!board) return;

  const reorderUrl = board.dataset.reorderUrl;
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value
    || document.querySelector("meta[name=csrf-token]")?.content;

  let draggedCard = null;

  function getCards(columnBody) {
    return [...columnBody.querySelectorAll("[data-task-id]")];
  }

  async function persist(taskId, columnId, orderedIds) {
    const response = await fetch(reorderUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({
        task_id: taskId,
        column_id: columnId,
        ordered_ids: orderedIds,
      }),
    });
    if (!response.ok) {
      console.error("Falha ao reordenar tarefa");
    }
  }

  board.querySelectorAll("[data-task-id]").forEach((card) => {
    card.addEventListener("dragstart", (event) => {
      draggedCard = card;
      card.classList.add("is-dragging");
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", card.dataset.taskId);
    });

    card.addEventListener("dragend", () => {
      card.classList.remove("is-dragging");
      board.querySelectorAll(".board-column").forEach((col) => {
        col.classList.remove("is-drag-over");
      });
      draggedCard = null;
    });
  });

  board.querySelectorAll("[data-column-id]").forEach((column) => {
    const body = column.querySelector("[data-column-body]");

    column.addEventListener("dragover", (event) => {
      event.preventDefault();
      column.classList.add("is-drag-over");
      const afterElement = getDragAfterElement(body, event.clientY);
      if (!draggedCard) return;
      if (afterElement == null) {
        body.appendChild(draggedCard);
      } else {
        body.insertBefore(draggedCard, afterElement);
      }
    });

    column.addEventListener("dragleave", (event) => {
      if (!column.contains(event.relatedTarget)) {
        column.classList.remove("is-drag-over");
      }
    });

    column.addEventListener("drop", (event) => {
      event.preventDefault();
      column.classList.remove("is-drag-over");
      if (!draggedCard) return;
      const orderedIds = getCards(body).map((el) => el.dataset.taskId);
      persist(draggedCard.dataset.taskId, column.dataset.columnId, orderedIds);
      const count = column.querySelector("[data-column-count]");
      if (count) count.textContent = String(orderedIds.length);
      board.querySelectorAll("[data-column-id]").forEach((col) => {
        const c = col.querySelector("[data-column-count]");
        const n = col.querySelectorAll("[data-task-id]").length;
        if (c) c.textContent = String(n);
      });
    });
  });

  function getDragAfterElement(container, y) {
    const elements = [...container.querySelectorAll("[data-task-id]:not(.is-dragging)")];
    return elements.reduce(
      (closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
          return { offset, element: child };
        }
        return closest;
      },
      { offset: Number.NEGATIVE_INFINITY, element: null }
    ).element;
  }
})();
