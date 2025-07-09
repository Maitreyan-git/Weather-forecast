document.querySelectorAll('.district').forEach(district => {
    district.addEventListener('mouseenter', () => {
        const districtName = district.getAttribute('data-district');
        console.log(`Hovered over ${districtName}`);
    });
});
