// const userLink = document.getElementById('user-link');
// const contentArea = document.querySelector('.content-area');

// const userForm = `
// <div class="form-group">
//     <label for="fullName">Full Name:</label>
//     <input type="text" id="fullName" name="fullName" required>
// </div>
// <div class="form-group">
//     <label for="dateOfBirth">Date of Birth:</label>
//     <input type="date" id="dateOfBirth" name="dateOfBirth" required>
// </div>
// <div class="form-group">
//     <label for="district">District:</label>
//     <input type="text" id="district" name="district" required>
// </div>
// <div class="form-group">
//     <label for="electionStatus">Election Status:</label>
//     <input type="text" id="electionStatus" name="electionStatus" required>
// </div>
// <div class="form-group">
//     <label for="role">Role:</label>
//     <input type="text" id="role" name="role" required>
// </div>
// <div class="form-group">
//     <label for="password">Password:</label>
//     <input type="password" id="password" name="password" required>
// </div>
// <button type="submit">Create</button>
// `;

// userLink.addEventListener('click', () => {
//   contentArea.innerHTML = userForm;
// });

function loadPage(page) {
    event.preventDefault();
    // Make an AJAX request to fetch the content of the page
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState == XMLHttpRequest.DONE) {
            if (xhr.status == 200) {
                // On success, update the content area with the loaded content
                // document.getElementById('main-content').innerHTML = "";
                document.getElementById('main-content').innerHTML = xhr.responseText;
            } else {
                // Handle error
                console.error('Failed to load page:', xhr.status);
            }
        }
    };
    xhr.open('GET', '/' + page, true);
    xhr.send();
}

