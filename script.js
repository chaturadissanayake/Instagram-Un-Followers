// script.js
$(document).ready(function() {
    // Handle form submission
    $('#tracker-form').on('submit', function(e) {
        e.preventDefault();
        
        // Get form data
        const username = $('#username').val();
        const password = $('#password').val();
        const target_account = $('#target_account').val();
        
        // Show progress UI
        $('#tracker-form').addClass('d-none');
        $('#progress-section').removeClass('d-none');
        $('#results-section').addClass('d-none');
        
        // Simulate progress animation
        simulateProgress();
        
        // Send request to backend
        $.ajax({
            url: '/track',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                username: username,
                password: password,
                target_account: target_account
            }),
            success: function(response) {
                // Handle success response
                if (response.error) {
                    showError(response.error);
                    return;
                }
                
                // Show results
                showResults(response);
            },
            error: function(xhr) {
                // Handle errors
                let errorMsg = "An error occurred. Please try again.";
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                showError(errorMsg);
            }
        });
    });
    
    // Track again button
    $('#track-again').on('click', function() {
        $('#results-section').addClass('d-none');
        $('#tracker-form').removeClass('d-none');
        $('#username').val('');
        $('#password').val('');
        $('#target_account').val('');
        $('#username').focus();
    });
    
    function simulateProgress() {
        let width = 0;
        const interval = setInterval(() => {
            if (width >= 90) {
                clearInterval(interval);
                return;
            }
            width += 5;
            $('#progress-bar').css('width', width + '%');
        }, 300);
    }
    
    function showError(message) {
        $('#progress-section').addClass('d-none');
        $('#tracker-form').removeClass('d-none');
        alert('Error: ' + message);
    }
    
    function showResults(data) {
        // Update counts
        $('#new-count').text(data.new_count);
        $('#unfollowers-count').text(data.unfollowers_count);
        
        // Set download links
        $('#download-new').attr('href', `/download/new_followers/${data.session_id}`);
        $('#download-unfollowers').attr('href', `/download/unfollowers/${data.session_id}`);
        
        // Complete progress bar
        $('#progress-bar').css('width', '100%');
        
        // Show results after delay for better UX
        setTimeout(() => {
            $('#progress-section').addClass('d-none');
            $('#results-section').removeClass('d-none');
        }, 800);
    }
});
