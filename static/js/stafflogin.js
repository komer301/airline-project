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

$(document).ready(function () {
  $("form.login").on("submit", function (event) {
    event.preventDefault(); // Prevent default form submission
    var form = $(this);
    $.ajax({
      url: "/stafflogin",
      type: "POST",
      data: form.serialize(),
      success: function (response) {
        alert(response.message);
        if (response.success) {
          window.location.href = "/"; // Redirect to login after signup
        }
      },
      error: function (response) {
        alert(response.responseJSON.message);
      },
    });
  });

  $("form.signup").on("submit", function (event) {
    event.preventDefault();
    var form = $(this);
    $.ajax({
      url: "/staffsignup",
      method: "POST",
      data: form.serialize(),
      success: function (response) {
        alert(response.message);
        if (response.success) {
          window.location.href = "/"; // Redirect to login after signup
        }
      },
      error: function (response) {
        alert(response.responseJSON.message);
      },
    });
  });
});
