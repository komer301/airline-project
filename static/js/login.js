const loginText = document.querySelector(".title-text .login");
const loginForm = document.querySelector("form.login");
const loginBtn = document.querySelector("label.login");
const signupBtn = document.querySelector("label.signup");
const signupLink = document.querySelector("form .signup-link a");

signupBtn.onclick = () => {
  loginForm.style.marginLeft = "-50%";
  loginText.style.marginLeft = "-50%";
};
loginBtn.onclick = () => {
  loginForm.style.marginLeft = "0%";
  loginText.style.marginLeft = "0%";
};
// signupLink.onclick = () => {
//   signupBtn.click();
//   return false;
// };

document
  .getElementById("user-type-signup")
  .addEventListener("change", function () {
    var userType = this.value;
    if (userType === "staff") {
      document.getElementById("username-field-signup").style.display = "block";
    } else {
      document.getElementById("username-field-signup").style.display = "none";
    }
  });

document
  .getElementById("user-type-login")
  .addEventListener("change", function () {
    var userType = this.value;
    if (userType === "staff") {
      document.getElementById("email-field").style.display = "none";
      document.getElementById("username-field").style.display = "block";
    } else {
      document.getElementById("email-field").style.display = "block";
      document.getElementById("username-field").style.display = "none";
    }
  });

// $(document).ready(function () {
//   $("form.login").on("submit", function (event) {
//     event.preventDefault(); // Prevent default form submission
//     var form = $(this);
//     $.ajax({
//       url: "/login",
//       type: "POST",
//       data: form.serialize(),
//       success: function (response) {
//         alert(response.message);
//         if (response.success) {
//           window.location.href = "/"; // Redirect to login after signup
//         }
//       },
//       error: function (response) {
//         alert(response.responseJSON.message);
//       },
//     });
//   });

//   $("form.signup").on("submit", function (event) {
//     event.preventDefault();
//     var form = $(this);
//     $.ajax({
//       url: "/signup",
//       method: "POST",
//       data: form.serialize(),
//       success: function (response) {
//         alert(response.message);
//         if (response.success) {
//           window.location.href = "/"; // Redirect to login after signup
//         }
//       },
//       error: function (response) {
//         alert(response.responseJSON.message);
//       },
//     });
//   });
// });
