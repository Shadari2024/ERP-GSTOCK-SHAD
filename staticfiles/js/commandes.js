function ajouterLigne() {
    const table = document.getElementById('ligne-commandes');
    const row = document.createElement('tr');
    row.classList.add('animate__animated', 'animate__fadeIn');
    row.innerHTML = `
      <td><input type="text" class="form-control" placeholder="Nom du produit"></td>
      <td><input type="number" class="form-control quantite" value="1" min="1" onchange="calculerTotal()"></td>
      <td><input type="number" class="form-control prix" value="0" step="0.01" onchange="calculerTotal()"></td>
      <td><input type="text" class="form-control" value="0%" disabled></td>
      <td class="montant">0.00</td>
      <td><button class="btn btn-danger btn-sm" onclick="supprimerLigne(this)"><i class="bi bi-trash"></i></button></td>
    `;
    table.appendChild(row);
    calculerTotal();
  }
  
  function supprimerLigne(btn) {
    btn.closest('tr').remove();
    calculerTotal();
  }
  
  function calculerTotal() {
    let total = 0;
    const lignes = document.querySelectorAll('#ligne-commandes tr');
    lignes.forEach(ligne => {
      const qte = parseFloat(ligne.querySelector('.quantite').value) || 0;
      const prix = parseFloat(ligne.querySelector('.prix').value) || 0;
      const montant = (qte * prix).toFixed(2);
      ligne.querySelector('.montant').innerText = montant;
      total += parseFloat(montant);
    });
    document.getElementById('ht').innerText = total.toFixed(2);
    document.getElementById('total').innerText = total.toFixed(2);
  }
  