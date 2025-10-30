// static/js/reflections.js - NOUVEAU FICHIER
class GuidedReflections {
    constructor(chatbot) {
        this.chatbot = chatbot;
        this.currentPrompt = '';
        this.currentType = 'emotion';
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Remplacer l'ancien modal par le nouveau système
        document.getElementById('newReflectionBtn').addEventListener('click', () => {
            this.showGuidedReflectionModal();
        });
    }

    async showGuidedReflectionModal() {
        // Créer le modal guidé
        this.createGuidedModal();
        
        // Charger un premier prompt
        await this.loadNewPrompt('emotion');
    }

    createGuidedModal() {
        // Supprimer l'ancien modal s'il existe
        const oldModal = document.getElementById('reflectionModal');
        if (oldModal) oldModal.remove();

        // Créer le nouveau modal guidé
        const modalHTML = `
        <div id="guidedReflectionModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
                <h3 class="text-xl font-semibold mb-4">📝 Nouvelle Réflexion Guidée</h3>
                
                <!-- Sélection du type -->
                <div class="mb-6">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Type de réflexion</label>
                    <div class="grid grid-cols-2 gap-3">
                        <button type="button" data-type="gratitude" 
                                class="reflection-type-btn p-3 border-2 border-gray-200 rounded-lg text-center hover:border-yellow-400 transition-colors">
                            <span class="text-2xl">😊</span>
                            <div class="text-sm font-medium mt-1">Gratitude</div>
                        </button>
                        <button type="button" data-type="emotion" 
                                class="reflection-type-btn p-3 border-2 border-gray-200 rounded-lg text-center hover:border-purple-400 transition-colors">
                            <span class="text-2xl">🎭</span>
                            <div class="text-sm font-medium mt-1">Émotions</div>
                        </button>
                        <button type="button" data-type="cycle" 
                                class="reflection-type-btn p-3 border-2 border-gray-200 rounded-lg text-center hover:border-pink-400 transition-colors">
                            <span class="text-2xl">🌙</span>
                            <div class="text-sm font-medium mt-1">Cycle</div>
                        </button>
                        <button type="button" data-type="mindfulness" 
                                class="reflection-type-btn p-3 border-2 border-gray-200 rounded-lg text-center hover:border-green-400 transition-colors">
                            <span class="text-2xl">🧘</span>
                            <div class="text-sm font-medium mt-1">Pleine conscience</div>
                        </button>
                    </div>
                </div>

                <!-- Prompt actuel -->
                <div class="mb-6">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Question guidée</label>
                    <div id="currentPrompt" class="p-4 bg-blue-50 rounded-lg border border-blue-200 text-gray-700">
                        Chargement...
                    </div>
                    <button id="newPromptBtn" 
                            class="mt-2 text-blue-600 hover:text-blue-800 text-sm font-medium">
                        🔄 Nouvelle question
                    </button>
                </div>

                <!-- Réponse utilisateur -->
                <div class="mb-6">
                    <label for="guidedReflectionContent" class="block text-sm font-medium text-gray-700 mb-2">Ta réponse</label>
                    <textarea id="guidedReflectionContent" 
                              rows="6"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                              placeholder="Écris ta réflexion ici..."></textarea>
                </div>

                <!-- Actions -->
                <div class="flex justify-end space-x-3">
                    <button type="button" 
                            id="cancelGuidedReflectionBtn"
                            class="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium">
                        Annuler
                    </button>
                    <button type="button" 
                            id="saveGuidedReflectionBtn"
                            class="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                        💫 Sauvegarder & Analyser
                    </button>
                </div>
            </div>
        </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.bindGuidedModalEvents();
    }

    bindGuidedModalEvents() {
        // Type selection
        document.querySelectorAll('.reflection-type-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const type = e.currentTarget.dataset.type;
                this.selectReflectionType(type);
            });
        });

        // Nouveau prompt
        document.getElementById('newPromptBtn').addEventListener('click', () => {
            this.loadNewPrompt(this.currentType);
        });

        // Sauvegarder
        document.getElementById('saveGuidedReflectionBtn').addEventListener('click', () => {
            this.saveGuidedReflection();
        });

        // Annuler
        document.getElementById('cancelGuidedReflectionBtn').addEventListener('click', () => {
            this.hideGuidedModal();
        });
    }

    async selectReflectionType(type) {
        this.currentType = type;
        
        // Mettre à jour le style des boutons
        document.querySelectorAll('.reflection-type-btn').forEach(btn => {
            btn.classList.remove('border-indigo-500', 'bg-indigo-50');
            if (btn.dataset.type === type) {
                btn.classList.add('border-indigo-500', 'bg-indigo-50');
            }
        });

        // Charger un nouveau prompt pour ce type
        await this.loadNewPrompt(type);
    }

    async loadNewPrompt(type) {
        try {
            const response = await fetch(`/chatbot/api/reflections/prompt/?type=${type}`);
            if (response.ok) {
                const data = await response.json();
                this.currentPrompt = data.prompt;
                document.getElementById('currentPrompt').textContent = this.currentPrompt;
            }
        } catch (error) {
            console.error('Error loading prompt:', error);
            document.getElementById('currentPrompt').textContent = "Erreur de chargement";
        }
    }

    async saveGuidedReflection() {
        const content = document.getElementById('guidedReflectionContent').value.trim();

        if (!content) {
            alert('Veuillez écrire votre réflexion');
            return;
        }

        this.chatbot.showLoading();
        try {
            const response = await fetch('/chatbot/api/reflections/guided/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.chatbot.getCSRFToken()
                },
                body: JSON.stringify({
                    title: `Réflexion ${this.currentType}`,
                    content: content,
                    reflection_type: this.currentType,
                    prompt_used: this.currentPrompt,
                    conversation: this.chatbot.currentConversationId
                })
            });

            if (response.ok) {
                const reflection = await response.json();
                this.hideGuidedModal();
                this.chatbot.loadReflections();
                this.chatbot.showSuccess('Réflexion sauvegardée avec analyse IA !');
                
                // Afficher l'analyse IA
                if (reflection.ai_analysis) {
                    setTimeout(() => {
                        alert(`💫 Analyse IA:\n\n${reflection.ai_analysis}`);
                    }, 500);
                }
            } else {
                throw new Error('Erreur lors de la sauvegarde');
            }
        } catch (error) {
            console.error('Error:', error);
            this.chatbot.showError('Erreur lors de la sauvegarde');
        } finally {
            this.chatbot.hideLoading();
        }
    }

    hideGuidedModal() {
        const modal = document.getElementById('guidedReflectionModal');
        if (modal) modal.remove();
    }
}

// Intégration dans le chatbot existant
// Dans chatbot.js, remplacer l'ancien système de réflexions
class Chatbot {
    constructor() {
        // ... code existant ...
        this.guidedReflections = new GuidedReflections(this);
    }

    // SUPPRIMER les anciennes méthodes showReflectionModal, hideReflectionModal, etc.
}