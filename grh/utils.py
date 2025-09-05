from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings
import os
from datetime import datetime
from decimal import Decimal
from django.utils import timezone

class BulletinPaiePDFGenerator:
    
    @staticmethod
    def generate_bulletin_pdf(bulletin):
        """Génère un bulletin de paie en PDF avec informations complètes de l'entreprise"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Ajout de styles personnalisés
        custom_styles = {
            'Header': ParagraphStyle(
                name='Header',
                fontSize=16,
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName='Helvetica-Bold'
            ),
            'SubHeader': ParagraphStyle(
                name='SubHeader',
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=6,
                textColor=colors.darkblue
            ),
            'BulletinTitle': ParagraphStyle(
                name='BulletinTitle',
                fontSize=14,
                alignment=TA_LEFT,
                spaceAfter=6,
                fontName='Helvetica-Bold',
                textColor=colors.darkblue
            ),
            'CompanyInfo': ParagraphStyle(
                name='CompanyInfo',
                fontSize=10,
                alignment=TA_CENTER,
                spaceAfter=3,
                textColor=colors.grey
            ),
            'SmallInfo': ParagraphStyle(
                name='SmallInfo',
                fontSize=8,
                alignment=TA_CENTER,
                spaceAfter=2,
                textColor=colors.grey
            )
        }
        
        for style_name, style in custom_styles.items():
            if style_name not in styles:
                styles.add(style)
        
        elements = []
        
        # ==================== EN-TÊTE AVEC INFORMATIONS COMPLÈTES DE L'ENTREPRISE ====================
        
        # Récupérer la devise principale depuis ConfigurationSAAS
        devise_symbole = "€"  # Valeur par défaut
        try:
            from parametres.models import ConfigurationSAAS
            config_saas = ConfigurationSAAS.objects.get(entreprise=bulletin.entreprise)
            if config_saas.devise_principale:
                devise_symbole = config_saas.devise_principale.symbole
        except:
            pass
        
        # Logo de l'entreprise (si disponible)
        logo_path = None
        if hasattr(bulletin.entreprise, 'logo') and bulletin.entreprise.logo:
            logo_path = bulletin.entreprise.logo.path
            if os.path.exists(logo_path):
                try:
                    logo = Image(logo_path, width=60, height=60)
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(Spacer(1, 10))
                except:
                    pass  # Si le logo ne peut pas être chargé
        
        # Nom de l'entreprise
        elements.append(Paragraph("BULLETIN DE PAIE", styles['Header']))
        elements.append(Paragraph(f"{bulletin.entreprise.nom.upper()}", styles['SubHeader']))
        
        # Informations complètes de l'entreprise
        company_info = []
        
        if hasattr(bulletin.entreprise, 'forme_juridique') and bulletin.entreprise.forme_juridique:
            company_info.append(bulletin.entreprise.forme_juridique)
        
        if hasattr(bulletin.entreprise, 'adresse') and bulletin.entreprise.adresse:
            company_info.append(bulletin.entreprise.adresse)
        
        if hasattr(bulletin.entreprise, 'ville') and bulletin.entreprise.ville:
            ville_info = bulletin.entreprise.ville
            if hasattr(bulletin.entreprise, 'code_postal') and bulletin.entreprise.code_postal:
                ville_info = f"{bulletin.entreprise.code_postal} {ville_info}"
            if hasattr(bulletin.entreprise, 'pays') and bulletin.entreprise.pays:
                ville_info = f"{ville_info}, {bulletin.entreprise.pays}"
            company_info.append(ville_info)
        
        # Informations de contact
        contact_info = []
        if hasattr(bulletin.entreprise, 'telephone') and bulletin.entreprise.telephone:
            contact_info.append(f"Tél: {bulletin.entreprise.telephone}")
        if hasattr(bulletin.entreprise, 'email') and bulletin.entreprise.email:
            contact_info.append(f"Email: {bulletin.entreprise.email}")
        if hasattr(bulletin.entreprise, 'site_web') and bulletin.entreprise.site_web:
            contact_info.append(f"Site: {bulletin.entreprise.site_web}")
        
        # Informations légales
        legal_info = []
        if hasattr(bulletin.entreprise, 'siret') and bulletin.entreprise.siret:
            legal_info.append(f"SIRET: {bulletin.entreprise.siret}")
        if hasattr(bulletin.entreprise, 'tva_intracommunautaire') and bulletin.entreprise.tva_intracommunautaire:
            legal_info.append(f"TVA Intra: {bulletin.entreprise.tva_intracommunautaire}")
        if hasattr(bulletin.entreprise, 'rcs') and bulletin.entreprise.rcs:
            legal_info.append(f"RCS: {bulletin.entreprise.rcs}")
        if hasattr(bulletin.entreprise, 'ape_naf') and bulletin.entreprise.ape_naf:
            legal_info.append(f"APE/NAF: {bulletin.entreprise.ape_naf}")
        
        # Ajout des informations au PDF
        for info in company_info:
            elements.append(Paragraph(info, styles['CompanyInfo']))
        
        if contact_info:
            elements.append(Paragraph(" | ".join(contact_info), styles['SmallInfo']))
        
        if legal_info:
            elements.append(Paragraph(" | ".join(legal_info), styles['SmallInfo']))
        
        elements.append(Paragraph(f"Devise: {devise_symbole}", styles['SmallInfo']))
        elements.append(Spacer(1, 15))
        
        # Ligne séparatrice
        elements.append(Paragraph("_" * 80, styles['CompanyInfo']))
        elements.append(Spacer(1, 15))
        
        # ==================== INFORMATIONS EMPLOYÉ ====================
        
        elements.append(Paragraph("INFORMATIONS DU SALARIÉ", styles['BulletinTitle']))
        
        employe_data = [
            ['Employé:', f"{bulletin.employe.nom_complet}"],
            ['Matricule:', bulletin.employe.matricule],
            ['Poste:', bulletin.employe.poste.intitule if bulletin.employe.poste else ''],
            ['Département:', bulletin.employe.poste.departement.nom if bulletin.employe.poste and bulletin.employe.poste.departement else ''],
            ['Date embauche:', bulletin.employe.date_embauche.strftime('%d/%m/%Y') if bulletin.employe.date_embauche else ''],
            ['Période:', bulletin.periode],
            ['Date édition:', bulletin.date_edition.strftime('%d/%m/%Y')],
            ['Contrat:', bulletin.contrat.reference if bulletin.contrat else '']
        ]
        
        employe_table = Table(employe_data, colWidths=[100, 250])
        employe_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(employe_table)
        elements.append(Spacer(1, 15))
        
        # ==================== DÉTAIL DES GAINS ====================
        
        elements.append(Paragraph("DÉTAIL DES GAINS", styles['BulletinTitle']))
        gains_data = [['Description', f'Montant ({devise_symbole})']]
        
        gains_lignes = bulletin.lignes.filter(type_ligne='GAINS').order_by('ordre')
        total_gains = Decimal('0')
        
        for ligne in gains_lignes:
            gains_data.append([ligne.libelle, f"{ligne.montant:.2f}"])
            total_gains += ligne.montant
        
        gains_data.append(['TOTAL GAINS', f"{total_gains:.2f}"])
        
        gains_table = Table(gains_data, colWidths=[350, 80])
        gains_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 10),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
        ]))
        elements.append(gains_table)
        elements.append(Spacer(1, 12))
        
        # ==================== DÉTAIL DES RETENUES ====================
        
        elements.append(Paragraph("DÉTAIL DES RETENUES", styles['BulletinTitle']))
        retenues_data = [['Description', f'Montant ({devise_symbole})']]
        
        retenues_lignes = bulletin.lignes.filter(type_ligne='RETENUES').order_by('ordre')
        total_retenues = Decimal('0')
        
        for ligne in retenues_lignes:
            retenues_data.append([ligne.libelle, f"{ligne.montant:.2f}"])
            total_retenues += ligne.montant
        
        retenues_data.append(['TOTAL RETENUES', f"{total_retenues:.2f}"])
        
        retenues_table = Table(retenues_data, colWidths=[350, 80])
        retenues_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 10),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
        ]))
        elements.append(retenues_table)
        elements.append(Spacer(1, 15))
        
        # ==================== RÉCAPITULATIF ====================
        
        elements.append(Paragraph("RÉCAPITULATIF", styles['BulletinTitle']))
        recap_data = [
            ['Salaire Brut:', f"{bulletin.salaire_brut:.2f} {devise_symbole}"],
            ['Total des Retenues:', f"{bulletin.total_cotisations:.2f} {devise_symbole}"],
            ['', ''],
            ['SALAIRE NET:', f"{bulletin.salaire_net:.2f} {devise_symbole}"],
            ['', ''],
            ['NET À PAYER:', f"{bulletin.net_a_payer:.2f} {devise_symbole}"]
        ]
        
        recap_table = Table(recap_data, colWidths=[200, 150])
        recap_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 11),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONT', (0, 3), (-1, 3), 'Helvetica-Bold', 12),
            ('FONT', (0, 5), (-1, 5), 'Helvetica-Bold', 14),
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#3498db')),
            ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 3), (-1, 3), colors.white),
            ('TEXTCOLOR', (0, 5), (-1, 5), colors.white),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(recap_table)
        elements.append(Spacer(1, 20))
        
        # ==================== INFORMATIONS COMPLÉMENTAIRES ====================
        
        elements.append(Paragraph("INFORMATIONS COMPLÉMENTAIRES", styles['BulletinTitle']))
        info_data = [
            ['Jours travaillés:', f"{bulletin.jours_travailles}"],
            ['Heures travaillées:', f"{bulletin.heures_travaillees:.2f} h"],
            ['Taux horaire moyen:', f"{(bulletin.salaire_brut / bulletin.heures_travaillees):.2f} {devise_symbole}/h" if bulletin.heures_travaillees > 0 else 'N/A'],
            ['Ancienneté:', f"{bulletin.employe.anciennete()} ans"],
            ['Statut:', bulletin.employe.get_statut_display() if hasattr(bulletin.employe, 'get_statut_display') else '']
        ]
        
        info_table = Table(info_data, colWidths=[150, 200])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # ==================== SIGNATURE ====================
        
        signature_data = [
            ['', ''],
            ['Le Salarié', "L'Employeur"],
            ['', ''],
            ['_________________________', '_________________________'],
            ['Nom et Signature', 'Nom et Signature'],
            ['', ''],
            ['Date: ___________________', f'Date: {timezone.now().strftime("%d/%m/%Y")}']
        ]
        
        signature_table = Table(signature_data, colWidths=[200, 200])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
            ('FONT', (0, 1), (-1, 1), 'Helvetica-Bold', 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(signature_table)
        
        # ==================== PIED DE PAGE ====================
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("_" * 80, styles['CompanyInfo']))
        
        footer_text = [
            f"Document généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}",
            f"{bulletin.entreprise.nom} - {bulletin.entreprise.siret if hasattr(bulletin.entreprise, 'siret') and bulletin.entreprise.siret else ''}",
            "Ce document fait foi de bulletin de paie officiel"
        ]
        
        for text in footer_text:
            elements.append(Paragraph(text, styles['SmallInfo']))
        
        # Génération du PDF
        doc.build(elements)
        
        buffer.seek(0)
        return buffer

    @staticmethod
    def save_bulletin_pdf(bulletin):
        """Sauvegarde le PDF généré dans le champ fichier_bulletin"""
        from django.core.files.base import ContentFile
        
        try:
            pdf_buffer = BulletinPaiePDFGenerator.generate_bulletin_pdf(bulletin)
            
            # Nom du fichier
            filename = f"bulletin_{bulletin.employe.matricule}_{bulletin.periode}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Sauvegarde du fichier
            if bulletin.fichier_bulletin:
                bulletin.fichier_bulletin.delete(save=False)
            
            bulletin.fichier_bulletin.save(filename, ContentFile(pdf_buffer.getvalue()))
            bulletin.save()
            
            return bulletin.fichier_bulletin
            
        except Exception as e:
            print(f"Erreur lors de la génération du PDF: {e}")
            import traceback
            traceback.print_exc()
            raise