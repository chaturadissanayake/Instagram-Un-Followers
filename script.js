$(document).ready(function() {
    // Handle form submission
    $('#track-form').on('submit', function(e) {
        e.preventDefault();
        const username = $('#username').val().trim();
        
        if (!username) {
            showError("Please enter a username");
            return;
        }
        
        // Show progress, hide other sections
        $('#form-section').slideUp();
        $('#error-section').hide();
        $('#progress-section').removeClass('d-none').slideDown();
        $('#results-section').hide();
        
        // Simulate progress animation
        simulateProgress();
        
        // Send request to backend
        $.ajax({
            url: '/track',
            method: 'POST',
            data: {
                username: username
            },
            success: function(response) {
                if (response.error) {
                    showError(response.error);
                    return;
                }
                
                // If it's the first run (baseline saved)
                if (response.message) {
                    $('#progress-section').slideUp();
                    $('#form-section').slideDown();
                    alert(response.message + " Current followers: " + response.current_count);
                    return;
                }
                
                // Show results
                showResults(response);
            },
            error: function(xhr) {
                let errorMsg = "An error occurred. Please try again later.";
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                showError(errorMsg);
            }
        });
    });
    
    // New track button
    $('#new-track').on('click', function() {
        $('#results-section').slideUp();
        $('#form-section').slideDown();
        $('#username').val('').focus();
    });
    
    // Try again button
    $('#try-again').on('click', function() {
        $('#error-section').slideUp();
        $('#form-section').slideDown();
    });
    
    // Save session button
    $('#save-data').on('click', function() {
        alert('Your session has been saved. Return anytime to see changes!');
    });
    
    function simulateProgress() {
        const $progressBar = $('.progress-bar');
        let width = 0;
        
        const interval = setInterval(() => {
            if (width >= 80) {
                clearInterval(interval);
                return;
            }
            width += 5;
            $progressBar.css('width', width + '%');
            
            // Update progress text
            if (width < 30) {
                $('#progress-text').text('Connecting to Instagram...');
            } else if (width < 60) {
                $('#progress-text').text('Fetching followers...');
            } else {
                $('#progress-text').text('Analyzing changes...');
            }
        }, 300);
    }
    
    function showError(message) {
        $('#progress-section').slideUp();
        $('#error-section').removeClass('d-none').slideDown();
        $('#error-message').text(message);
    }
    
    function showResults(data) {
        // Update counts
        $('#new-count').text(data.new_count);
        $('#unfollowers-count').text(data.unfollowers_count);
        
        // Update sample lists
        const $newList = $('#new-list').empty();
        const $unfollowersList = $('#unfollowers-list').empty();
        
        if (data.new_followers && data.new_followers.length > 0) {
            data.new_followers.forEach(user => {
                $newList.append(`<li>${user}</li>`);
            });
        } else {
            $newList.append('<li class="text-muted">No new followers</li>');
        }
        
        if (data.unfollowers && data.unfollowers.length > 0) {
            data.unfollowers.forEach(user => {
                $unfollowersList.append(`<li>${user}</li>`);
            });
        } else {
            $unfollowersList.append('<li class="text-muted">No unfollowers</li>');
        }
        
        // Set download links
        $('#download-new').attr('href', `/download/new/${data.session_id}`);
        $('#download-unfollowers').attr('href', `/download/unfollowers/${data.session_id}`);
        
        // Show results after a small delay
        setTimeout(() => {
            $('#progress-section').slideUp();
            $('#results-section').removeClass('d-none').slideDown();
        }, 500);
    }
});
