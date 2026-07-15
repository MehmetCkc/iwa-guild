document.addEventListener("DOMContentLoaded", function () {
    const flashMessages = document.querySelectorAll(".flash-message");

    flashMessages.forEach(function (message) {
        setTimeout(function () {
            message.style.transition = "opacity 0.5s";
            message.style.opacity = "0";

            setTimeout(function () {
                message.remove();
            }, 500);
        }, 3000);
    });
});


// Search and filter quests on the home page
document.addEventListener("DOMContentLoaded", function () {
    const search = document.querySelector("#quest-search");
    const typeFilter = document.querySelector("#quest-type-filter");
    const difficultyFilter = document.querySelector("#difficulty-filter");
    const dayFilter = document.querySelector("#day-filter");
    const questCards = document.querySelectorAll(".quest-board .quest-card");

    if (!search || !typeFilter || !difficultyFilter || !dayFilter) {
        return;
    }

    function filterQuests() {
        const searchValue = search.value.toLowerCase();
        const selectedType = typeFilter.value.toLowerCase();
        const selectedDifficulty = difficultyFilter.value.toLowerCase();
        const selectedDay = dayFilter.value;

        questCards.forEach(function (card) {
            const matchesSearch = card.dataset.search.includes(searchValue);
            const matchesType = !selectedType || card.dataset.type === selectedType;
            const matchesDifficulty = !selectedDifficulty || card.dataset.difficulty === selectedDifficulty;
            const matchesDay = !selectedDay || card.dataset.days.split(",").includes(selectedDay);

            card.hidden = !(matchesSearch && matchesType && matchesDifficulty && matchesDay);
        });
    }

    search.addEventListener("input", filterQuests);
    typeFilter.addEventListener("change", filterQuests);
    difficultyFilter.addEventListener("change", filterQuests);
    dayFilter.addEventListener("change", filterQuests);
});


// Calendar on quest detail page
document.addEventListener("DOMContentLoaded", () => {
    const calendar = document.querySelector(".calendar-detailed");
    if (!calendar) {
        return;
    }

    const calendarButtons = document.querySelectorAll(".calendar-btn");
    const sessionCards = document.querySelectorAll(".session-card");
    const emptyState = document.querySelector("#no-sessions");

    calendar.addEventListener("click", (event) => {
        const clickedButton = event.target.closest(".calendar-btn");

        if (!clickedButton || !calendar.contains(clickedButton)) {
            return;
        }

        const selectedDay = Number(clickedButton.dataset.day);

        if (!Number.isInteger(selectedDay) || selectedDay < 1 || selectedDay > 7) {
            return;
        }

        calendarButtons.forEach((button) => {
            const isSelected = Number(button.dataset.day) === selectedDay;
            button.classList.toggle("has-selected", isSelected);
            button.setAttribute("aria-pressed", String(isSelected));
        });

        let visibleSessions = 0;

        sessionCards.forEach((card) => {
            const shouldShow = Number(card.dataset.day) === selectedDay;
            card.hidden = !shouldShow;

            if (shouldShow) {
                visibleSessions += 1;
            }
        });

        if (emptyState) {
            emptyState.hidden = visibleSessions > 0;
        }

        const url = new URL(window.location.href);
        url.searchParams.set("day", String(selectedDay));
        window.history.replaceState({ day: selectedDay }, "", url);
    });
});
