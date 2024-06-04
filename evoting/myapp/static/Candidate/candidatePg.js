function previewImage(event, elementId) {
    var reader = new FileReader();
    reader.onload = function() {
        var output = document.getElementById(elementId);
        output.src = reader.result;
        output.style.display = 'block';
    }
    reader.readAsDataURL(event.target.files[0]);
}

function openEditPopup() {
    var popup = document.getElementById("editPopup");
    var infoText = document.getElementById("informationDisplay").innerText;
    document.getElementById("editInformation").value = infoText;
    popup.style.display = "flex";
}

function closeEditPopup() {
    document.getElementById("editPopup").style.display = "none";
}

function updateInformation() {
    var updatedInfo = document.getElementById("editInformation").value;
    document.getElementById("informationDisplay").innerText = updatedInfo;
    closeEditPopup();
}

function deleteInformation() {
    document.getElementById("informationDisplay").innerText = "Type your information here...";
    closeEditPopup();
}

function openProfilePopup() {
    var popup = document.getElementById("profilePopup");
    var profilePictureSrc = document.getElementById("profilePictureDisplay").src;
    document.getElementById("profilePopupPicture").src = profilePictureSrc;
    popup.style.display = "flex";
}

function closeProfilePopup() {
    document.getElementById("profilePopup").style.display = "none";
}

function uploadProfilePicture() {
    var updatedProfileSrc = document.getElementById("profilePopupPicture").src;
    document.getElementById("profilePictureDisplay").src = updatedProfileSrc;
    closeProfilePopup();
}

function deleteProfilePicture() {
    var defaultSrc = "{% static 'images/default-profile.png' %}";
    document.getElementById("profilePopupPicture").src = defaultSrc;
    document.getElementById("profilePictureDisplay").src = defaultSrc;
    closeProfilePopup();
}

function openPosterPopup() {
    var popup = document.getElementById("posterPopup");
    var posterPictureSrc = document.getElementById("posterPictureDisplay").src;
    document.getElementById("posterPopupPicture").src = posterPictureSrc;
    popup.style.display = "flex";
}

function closePosterPopup() {
    document.getElementById("posterPopup").style.display = "none";
}

function uploadPosterPicture() {
    var updatedPosterSrc = document.getElementById("posterPopupPicture").src;
    document.getElementById("posterPictureDisplay").src = updatedPosterSrc;
    closePosterPopup();
}

function deletePosterPicture() {
    var defaultSrc = "{% static 'images/default-poster.png' %}";
    document.getElementById("posterPopupPicture").src = defaultSrc;
    document.getElementById("posterPictureDisplay").src = defaultSrc;
    closePosterPopup();
}

// JavaScript for previewing image before upload

// document.addEventListener('DOMContentLoaded', function() {
//     const form = document.getElementById('profilePicForm');
//     const input = form.querySelector('input[type="file"]');

//     input.addEventListener('change', function(event) {
//         if (input.files && input.files[0]) {
//             const reader = new FileReader();
//             reader.onload = function(e) {
//                 document.getElementById('profilePopupPicture').src = e.target.result;
//             };
//             reader.readAsDataURL(input.files[0]);
//         }
//     });
// });

document.addEventListener('DOMContentLoaded', function() {
    const profileForm = document.getElementById('profilePicForm');
    const profileInput = profileForm.querySelector('input[type="file"]');
    const posterForm = document.getElementById('electionPosterForm');
    const posterInput = posterForm.querySelector('input[type="file"]');
    
    const previewImage = function(input, previewElementId) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById(previewElementId).src = e.target.result;
            };
            reader.readAsDataURL(input.files[0]);
        }
    };

    profileInput.addEventListener('change', function(event) {
        previewImage(profileInput, 'profilePopupPicture');
    });

    posterInput.addEventListener('change', function(event) {
        previewImage(posterInput, 'posterPopupPicture');
    });
});
