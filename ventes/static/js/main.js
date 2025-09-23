// static/js/main.js

// S'assure que le DOM est prêt avant d'exécuter le code
$(document).ready(function () {
    console.log("✅ main.js chargé correctement");

    const $barcodeInput = $("#barcode-scanner");
    const $resultBox = $("#barcode-result");
    const $message = $("#barcode-message");
    const $error = $("#barcode-error");

    // Cacher les messages au démarrage
    $resultBox.hide();
    $error.hide();

    // Déclenche la recherche au scan ou sur "Entrée"
    $barcodeInput.on("keypress", function (e) {
        if (e.which === 13) {
            e.preventDefault();
            let code = $(this).val().trim();

            if (!code) {
                $error.text("Veuillez entrer un code-barres.");
                $error.show();
                return;
            }

            console.log("🔍 Recherche produit pour code :", code);

            $.ajax({
                url: `/ventes/api/search-by-barcode/?barcode=${encodeURIComponent(code)}`,
                type: "GET",
                dataType: "json",
                beforeSend: function () {
                    $message.text("Recherche en cours...");
                    $resultBox.show();
                    $error.hide();
                },
                success: function (data) {
                    if (data.success) {
                        if (data.multiple) {
                            $message.html(
                                `<b>${data.products.length}</b> produits trouvés. Veuillez sélectionner.`
                            );
                        } else {
                            let p = data.product;
                            $message.html(
                                `<b>${p.nom}</b> - Prix: <b>${p.prix_vente.toFixed(2)} $</b> | Stock: ${p.stock}`
                            );
                        }
                        $resultBox.show();
                    } else {
                        $error.text(data.message || "Produit introuvable.");
                        $error.show();
                        $resultBox.hide();
                    }
                },
                error: function (xhr) {
                    console.error("❌ Erreur API :", xhr.responseText);
                    $error.text("Erreur serveur : impossible de récupérer le produit.");
                    $error.show();
                    $resultBox.hide();
                },
                complete: function () {
                    // Réinitialiser le champ pour le prochain scan
                    $barcodeInput.val("");
                    $barcodeInput.focus();
                }
            });
        }
    });
});
