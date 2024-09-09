    // Helper function to format date as d-m-Y
    function formatDate(dateString) {
        const date = new Date(dateString);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-based
        const year = date.getFullYear();
        return `${day}-${month}-${year}`;
    }

    // Format posting dates
    document.querySelectorAll('.posting-date').forEach(function (element) {
        const originalDate = element.textContent.trim();
        element.textContent = formatDate(originalDate);
    });

    // Format start dates
    document.querySelectorAll('.start-date').forEach(function (element) {
        const originalDate = element.textContent.trim();
        element.textContent = formatDate(originalDate);
    });

    // Format end dates
    document.querySelectorAll('.end-date').forEach(function (element) {
        const originalDate = element.textContent.trim();
        element.textContent = formatDate(originalDate);
    });

