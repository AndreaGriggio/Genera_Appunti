from programmi_costruzione_appunti import estrai_txt_da_pdf_e_lancia_prompt
from programmi_costruzione_appunti.branch_explorer import elimina_txt,elimina_pdf
from API_Notion.inserisci_appunti import inserisci_appunti,elimina_risposte
from programmi_costruzione_appunti.branch_updater import BranchUpdater
from API_Notion.get_notion_branching import get_notion_branching
if __name__ == "__main__" :
  #elimina_txt()
  #elimina_risposte()
  #get_notion_branching()
  #BranchUpdater()

  estrai_txt_da_pdf_e_lancia_prompt()

  inserisci_appunti()
  #elimina_pdf()
  