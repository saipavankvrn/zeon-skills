document.addEventListener("DOMContentLoaded", function () {
  const header = document.getElementById("mainHeader");

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
});

document.addEventListener("DOMContentLoaded", function () {
  const header = document.getElementById("header2");

  // Set initial background color
  header.style.backgroundColor = "#ffffffff";
  header.style.boxShadow = "0px 0px 6px 2px #d4e6ff";
  header.style.transition = "background-color 0.3s ease";

  // Add scroll listener
  window.addEventListener("scroll", function () {
    if (window.scrollY > 50) {
      header.style.backgroundColor = "#ffffff";
    } else {
      header.style.backgroundColor = "#ffffffff";
    }
  });
});


// function adjustFooter() {
//   const footer = document.querySelector('section.bg-dark');
//   if (!footer) return;

//   const viewportHeight = window.innerHeight;
//   const footerTop = footer.getBoundingClientRect().top;
//   const footerHeight = footer.offsetHeight;

//   const footerBottom = footerTop + footerHeight;
//   const gap = viewportHeight - footerBottom;

//   if (gap > 0) {
//     footer.style.paddingBottom = gap + 'px';
//   } else {
//     footer.style.paddingBottom = '0px';
//   }
// }

// Run on page load and window resize
// window.addEventListener('load', adjustFooter);
// window.addEventListener('resize', adjustFooter);

const loginForm = document.getElementById("loginForm");
const loginCard = document.getElementById("loginCard");
const otpCard = document.getElementById("otpCard");

loginForm.addEventListener("submit", function (e) {
  e.preventDefault(); // stop form submit refresh
  // ✅ TODO: Send OTP to email with backend API here
  loginCard.classList.add("d-none"); // hide login
  otpCard.classList.remove("d-none"); // show otp
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

