

frappe.ready(function() {
    frappe.call({
    method: "custom_app.custom_script.get_valid_skill_options",
    callback: function(response) {
        var validOptions = response.message || [];

        $('[data-fieldname="skill_data"]').on('blur', function() {
            var enteredValues = $(this).val() || '';
            var enteredOptions = enteredValues.split(',');

            // Trim each option to remove leading and trailing whitespace
            enteredOptions = enteredOptions.map(function(option) {
                return option.trim();
            });

            // Remove duplicate entries
            enteredOptions = enteredOptions.filter(function(value, index, self) {
                return self.indexOf(value) === index;
            });

            console.log("Entered options after removing duplicates:", enteredOptions);

            // Filter out any invalid selections
            var validOptionsOnly = enteredOptions.filter(function(value) {
                return validOptions.includes(value);
            });

            console.log("Valid options only:", validOptionsOnly);

            if (validOptionsOnly.length !== enteredOptions.length) {
                $(this).val(validOptionsOnly.join(',')).trigger('change');
            }
        });
    }
});

   // Function to handle form submission
    var handleFormSubmission = function(event) {
        event.preventDefault(); // Prevent default form submission
        
        var formData = {};
        // Get field values from the form
        
 	console.log(formData)
        var email_id = $("input[data-fieldname='email_id']").val(); // Get value of read-only field
        // console.log(customer_id); // Debug statement
        var job_title = $("input[data-fieldname='job_title']").val(); // Get form_id from the form
        var skills = $("input[data-fieldname='skill_data']").val(); // Get form_id from the form
 
        // Check if customer_id and form_id are provided
        console.log("Email ID:", email_id);
	console.log("Job Title:", job_title);

 
        // Check if there's already a form with the same customer_id and form_id
        frappe.call({
            method: "custom_app.custom_script.validate_job_application",
            args: {
                job_title: job_title,
                email: email_id
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(r.message);
                } else {
                    // If validation passes, submit the form
                    $(".web-form-container form").submit();
                }
            }
        });
 
        return false; // Prevent default form submission
    };
 
    // Attach event listener to form submission button
    $(".submit-btn").click(function(event) {
        handleFormSubmission(event);
    });
    $("input[data-fieldname='job_title']").prop('readonly', true);
    $("input[data-fieldname='job_titles']").prop('readonly', true);
    // $("input[data-fieldname='job_type']").prop('readonly', true);
});
 
