// Email form submit → show OTP form
document.addEventListener("DOMContentLoaded", function () {
  let loginForm = document.getElementById("login-email");
  let otpForm = document.getElementById("login-otp");
  let emailInput = document.getElementById("email");

  if (loginForm) {   // ✅ check if element exists
    loginForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const email = emailInput.value.trim();

      if (email === "") {
        alert("Please enter your email.");
        return;
      }

      if (email.includes("@") && email.includes(".")) {
        loginForm.classList.add("d-none");
        otpForm.classList.remove("d-none");
      } else {
        alert("Please enter a valid email.");
      }
    });
  } else {
    console.error("login-email form not found in DOM.");
  }
});


  //to repeat questions 40 times


document.addEventListener("DOMContentLoaded", function () {
    let questionCount = 0;
    const maxQuestions = 40;

    const addQuestionBtn = document.getElementById("addQuestionBtn");
    const container = document.getElementById("questionsContainer");

  addQuestionBtn.addEventListener("click", function () {
    if (questionCount >= maxQuestions) {
      alert("You can only add up to 40 questions.");
      return;
    }

    questionCount++;

    const newCard = document.createElement("div");
    newCard.classList.add("skills-card", "mb-4");
    newCard.innerHTML = `
      <div class="section-header p-2">
        <h5><b>Questions & Answers</b></h5>
        <h6><b>Question ${questionCount}</b></h6>

        <input type="text" class="form-control mb-3" placeholder="Enter question">

        <div class="d-flex gap-2 mb-2">
          <input type="text" class="form-control" placeholder="Option A">
          <input type="text" class="form-control" placeholder="Option B">
        </div>
        <div class="d-flex gap-2 mb-2">
          <input type="text" class="form-control" placeholder="Option C">
          <input type="text" class="form-control" placeholder="Option D">
        </div>

        <label class="form-label">Correct Answer</label>
        <select class="form-select text-muted">
          <option disabled selected>Select Correct Answer</option>
          <option>Option A</option>
          <option>Option B</option>
          <option>Option C</option>
          <option>Option D</option>
        </select>
      </div>
    `;

    container.appendChild(newCard);
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const saveCategoryBtn = document.getElementById("saveCategoryBtn");
  const categoryInput = document.getElementById("categoryName");
  const categoriesTableBody = document.getElementById("categoriesTableBody");

  saveCategoryBtn.addEventListener("click", () => {
    const categoryName = categoryInput.value.trim();

    if (categoryName) {
      // Send new category to Flask
      fetch("/add_category", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: categoryName })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          // Add row to table
          const newRow = document.createElement("tr");
          newRow.innerHTML = `
            <td>${categoriesTableBody.rows.length + 1}</td>
            <td>${categoryName}</td>
          `;
          categoriesTableBody.appendChild(newRow);

          categoryInput.value = "";

          // Close modal
          const modalElement = document.getElementById("addCategoryModal");
          const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
          modal.hide();
        } else {
          alert("Failed to save category. It may already exist.");
        }
      });
    } else {
      alert("Please enter a category name");
    }
  });
});
