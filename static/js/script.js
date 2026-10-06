document.addEventListener("DOMContentLoaded", function () {
  const header = document.getElementById("mainHeader");
  if (header) {
    // Set initial background color
    header.style.backgroundColor = "#d4e6ff";
    header.style.boxShadow = "0px 0px 6px 2px #d4e6ff";
    header.style.transition = "background-color 0.3s ease";

    // Add scroll listener
    window.addEventListener("scroll", function () {
      if (window.scrollY > 50) {
        header.style.backgroundColor = "#ffffff";
      } else {
        header.style.backgroundColor = "#d4e6ff";
      }
    });
  }

  const header2 = document.getElementById("header2");
  if (header2) {
    // Set initial background color
    header2.style.backgroundColor = "#ffffff";
    header2.style.boxShadow = "0px 0px 6px 2px rgba(0, 0, 0, 0.08)";
    header2.style.transition = "background-color 0.3s ease";

    // Add scroll listener
    window.addEventListener("scroll", function () {
      if (window.scrollY > 50) {
        header2.style.backgroundColor = "#ffffff";
      } else {
        header2.style.backgroundColor = "#ffffff";
      }
    });
  }

  const loginForm = document.getElementById("loginForm");
  const loginCard = document.getElementById("loginCard");
  const otpCard = document.getElementById("otpCard");

  if (loginForm && loginCard && otpCard) {
    loginForm.addEventListener("submit", function (e) {
      e.preventDefault();
      loginCard.classList.add("d-none");
      otpCard.classList.remove("d-none");
    });
  }
});



function showQuestion(n) {
    const el = document.getElementById('q' + n);
    if (!el) {
        console.warn('Question not found:', n);
        return;
    }
    document.querySelectorAll('.question').forEach(q => q.classList.remove('active'));
    el.classList.add('active');
}
function nextQuestion(n) { showQuestion(n + 1); }
function prevQuestion(n) { showQuestion(n - 1); }
function submitQuiz() { alert("Quiz Submitted!"); }

