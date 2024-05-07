frappe.ready(function() {
    // Function to handle form submission
    var handleFormSubmission = function(event) {
        event.preventDefault(); // Prevent default form submission
        
        var formData = {};
        // Get field values from the form
        
 	console.log(formData)
        var email_id = $("input[data-fieldname='email_id']").val(); // Get value of read-only field
        // console.log(customer_id); // Debug statement
        var job_title = $("input[data-fieldname='job_title']").val(); // Get form_id from the form
 
        // Check if customer_id and form_id are provided
        console.log(email_id,job_title)
 
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
    $("input[data-fieldname='job_type']").prop('readonly', true);
});
 