function filterTable() {
    const input = document.getElementById("searchInput").value.toLowerCase();
    document.querySelectorAll("#dataTable tbody tr").forEach(row => {
        row.style.display = row.innerText.toLowerCase().includes(input) ? "" : "none";
    });
}
