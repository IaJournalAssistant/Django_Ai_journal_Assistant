class Chatbot {
    constructor() {
        this.currentConversationId = null;
        this.conversations = [];
        this.reflections = [];
        this.baseURL = '/chatbot'; // ✅ URL de base
        this.init();
    }

 init() {
        this.bindEvents();
        this.loadConversations();
        this.loadReflections();
    }

    bindEvents() {
        document.getElementById('newConversationBtn').addEventListener('click', () => {
            this.createNewConversation();
        });

        document.getElementById('messageForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        document.getElementById('newReflectionBtn').addEventListener('click', () => {
            this.showReflectionModal();
        });

        document.getElementById('cancelReflectionBtn').addEventListener('click', () => {
            this.hideReflectionModal();
        });

        document.getElementById('reflectionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveReflection();
        });

        document.getElementById('messageInput').addEventListener('input', (e) => {
            const sendButton = document.getElementById('sendButton');
            sendButton.disabled = !e.target.value.trim();
        });
    }

       async createNewConversation() {
        this.showLoading();
        try {
            const response = await fetch(`${this.baseURL}/api/conversations/create/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({})
            });

            if (response.ok) {
                const conversation = await response.json();
                await this.loadConversations();
                this.selectConversation(conversation.id);
                this.showSuccess('Nouvelle conversation créée !');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Erreur lors de la création');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }


      async loadConversations() {
        try {
            const response = await fetch(`${this.baseURL}/api/conversations/`);
            if (response.ok) {
                this.conversations = await response.json();
                this.renderConversations();
            } else {
                throw new Error('Erreur ' + response.status);
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
            this.renderConversations();
        }
    }


     renderConversations() {
        const conversationsList = document.getElementById('conversationsList');
        
        if (!this.conversations || this.conversations.length === 0) {
            conversationsList.innerHTML = `
                <div class="text-center py-4 text-gray-500">
                    Aucune conversation. Cliquez sur "Nouvelle" pour commencer.
                </div>
            `;
            return;
        }

        conversationsList.innerHTML = this.conversations.map(conversation => `
            <div class="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors ${
                this.currentConversationId === conversation.id ? 'border-indigo-500 bg-indigo-50' : ''
            }">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="font-medium text-gray-900 text-sm truncate flex-1 cursor-pointer"
                        onclick="chatbot.selectConversation(${conversation.id})">
                        ${this.escapeHtml(conversation.title)}
                    </h4>
                    <button onclick="chatbot.deleteConversation(${conversation.id})" 
                            class="text-red-500 hover:text-red-700 ml-2 p-1 rounded transition-colors"
                            title="Supprimer">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                        </svg>
                    </button>
                </div>
                <div class="flex justify-between items-center text-xs text-gray-500">
                    <span>${new Date(conversation.updated_at).toLocaleDateString()}</span>
                    <span>${conversation.messages ? conversation.messages.length : 0} messages</span>
                </div>
            </div>
        `).join('');
    }

       async selectConversation(conversationId) {
        this.showLoading();
        try {
            const response = await fetch(`${this.baseURL}/api/conversations/${conversationId}/`);
            if (response.ok) {
                const conversation = await response.json();
                this.currentConversationId = conversationId;
                this.loadConversationData(conversation);
                this.renderConversations();
            } else {
                throw new Error('Erreur ' + response.status);
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('Erreur lors du chargement');
        } finally {
            this.hideLoading();
        }
    }

    loadConversationData(conversation) {
        // Activer l'input
        document.getElementById('messageInput').disabled = false;
        document.getElementById('sendButton').disabled = true;
        
        // Mettre à jour l'interface
        document.getElementById('conversationTitle').textContent = conversation.title;
        document.getElementById('currentConversationId').value = conversation.id;
        
        // Afficher les messages
        this.renderMessages(conversation.messages || []);
    }

    renderMessages(messages) {
        const messagesContainer = document.getElementById('messagesContainer');
        
        if (messages.length === 0) {
            messagesContainer.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    Aucun message. Commencez la conversation...
                </div>
            `;
            return;
        }

        messagesContainer.innerHTML = messages.map(message => `
            <div class="flex ${message.is_user ? 'justify-end' : 'justify-start'}">
                <div class="max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.is_user 
                        ? 'bg-indigo-600 text-white' 
                        : 'bg-gray-200 text-gray-900'
                }">
                    <div class="text-sm">${this.escapeHtml(message.text)}</div>
                    <div class="text-xs mt-1 opacity-70 ${
                        message.is_user ? 'text-indigo-100' : 'text-gray-600'
                    }">
                        ${new Date(message.created_at).toLocaleTimeString()}
                    </div>
                </div>
            </div>
        `).join('');

        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async deleteConversation(conversationId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cette conversation ?')) {
            return;
        }

        this.showLoading();
        try {
            // ✅ CORRIGÉ : Utiliser this.baseURL
            const response = await fetch(`${this.baseURL}/api/conversations/${conversationId}/delete/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                // Si on supprime la conversation actuelle, réinitialiser l'interface
                if (this.currentConversationId === conversationId) {
                    this.currentConversationId = null;
                    document.getElementById('conversationTitle').textContent = 'Sélectionnez une conversation';
                    document.getElementById('messageInput').disabled = true;
                    document.getElementById('sendButton').disabled = true;
                    document.getElementById('messagesContainer').innerHTML = `
                        <div class="text-center text-gray-500 py-8">
                            Commencez une nouvelle conversation ou sélectionnez-en une existante
                        </div>
                    `;
                }
                
                await this.loadConversations();
                this.showSuccess('Conversation supprimée avec succès');
            } else {
                throw new Error('Erreur lors de la suppression');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('Erreur lors de la suppression de la conversation');
        } finally {
            this.hideLoading();
        }
    }

   async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message || !this.currentConversationId) return;

        // Ajouter le message de l'utilisateur immédiatement
        this.addMessage(message, true);
        messageInput.value = '';
        document.getElementById('sendButton').disabled = true;

        this.showTypingIndicator();

        try {
            // ✅ CORRIGÉ : Utiliser this.baseURL
            const response = await fetch(`${this.baseURL}/api/conversations/${this.currentConversationId}/ai-response/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    message: message
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.hideTypingIndicator();
                
                // Recharger la conversation pour avoir les messages à jour
                await this.selectConversation(this.currentConversationId);
                
                if (data.conversation && data.conversation.title !== 'Nouvelle conversation') {
                    document.getElementById('conversationTitle').textContent = data.conversation.title;
                }
            } else {
                throw new Error('Erreur lors de la génération de la réponse');
            }
        } catch (error) {
            console.error('Error:', error);
            this.hideTypingIndicator();
            this.addMessage("Désolé, je rencontre des difficultés techniques. Pouvez-vous réessayer ?", false);
            this.showError('Erreur lors de l\'envoi du message');
        }
    }

    addMessage(text, isUser) {
        const messagesContainer = document.getElementById('messagesContainer');
        
        // Supprimer le message de bienvenue s'il existe
        if (messagesContainer.children.length === 1 && 
            messagesContainer.children[0].classList.contains('text-center')) {
            messagesContainer.innerHTML = '';
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'}`;
        
        messageDiv.innerHTML = `
            <div class="max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                isUser 
                    ? 'bg-indigo-600 text-white' 
                    : 'bg-gray-200 text-gray-900'
            }">
                <div class="text-sm">${this.escapeHtml(text)}</div>
                <div class="text-xs mt-1 opacity-70 ${
                    isUser ? 'text-indigo-100' : 'text-gray-600'
                }">
                    ${new Date().toLocaleTimeString()}
                </div>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

   async loadReflections() {
        try {
            // ✅ CORRIGÉ : Utiliser this.baseURL
            const response = await fetch(`${this.baseURL}/api/reflections/`);
            if (response.ok) {
                this.reflections = await response.json();
                this.renderReflections();
            }
        } catch (error) {
            console.error('Error loading reflections:', error);
        }
    }

     renderReflections() {
        const reflectionsList = document.getElementById('reflectionsList');
        
        if (!this.reflections || this.reflections.length === 0) {
            reflectionsList.innerHTML = `
                <div class="text-center text-gray-500 py-4 text-sm">
                    Aucune réflexion sauvegardée
                </div>
            `;
            return;
        }

        reflectionsList.innerHTML = this.reflections.map(reflection => `
            <div class="p-3 bg-gray-50 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-100 transition-colors"
                 onclick="chatbot.viewReflection(${reflection.id})">
                <h4 class="font-medium text-gray-900 text-sm truncate">${this.escapeHtml(reflection.title)}</h4>
                <p class="text-xs text-gray-500 mt-1 line-clamp-2">${this.escapeHtml(reflection.content)}</p>
                <div class="text-xs text-gray-400 mt-2">
                    ${new Date(reflection.created_at).toLocaleDateString()}
                </div>
            </div>
        `).join('');
    }

    showReflectionModal() {
        document.getElementById('reflectionModal').classList.remove('hidden');
        document.getElementById('reflectionTitle').value = '';
        document.getElementById('reflectionContent').value = '';
    }

    hideReflectionModal() {
        document.getElementById('reflectionModal').classList.add('hidden');
    }

     async saveReflection() {
        const title = document.getElementById('reflectionTitle').value.trim();
        const content = document.getElementById('reflectionContent').value.trim();

        if (!title || !content) {
            this.showError('Veuillez remplir tous les champs');
            return;
        }

        this.showLoading();
        try {
            const response = await fetch(`${this.baseURL}/api/reflections/create/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    title: title,
                    content: content,
                    conversation: this.currentConversationId,
                    // ✅ AJOUTER les champs requis avec valeurs par défaut
                    reflection_type: 'emotion',
                    mood: '',
                    ai_analysis: '',
                    prompt_used: ''
                })
            });

            if (response.ok) {
                this.hideReflectionModal();
                this.loadReflections();
                this.showSuccess('Réflexion sauvegardée avec succès');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Erreur lors de la sauvegarde');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    viewReflection(reflectionId) {
        const reflection = this.reflections.find(r => r.id === reflectionId);
        if (reflection) {
            alert(`Réflexion: ${reflection.title}\n\n${reflection.content}`);
        }
    }

    showTypingIndicator() {
        document.getElementById('typingIndicator').classList.remove('hidden');
        const messagesContainer = document.getElementById('messagesContainer');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        document.getElementById('typingIndicator').classList.add('hidden');
    }

    showLoading() {
        document.getElementById('loadingSpinner').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loadingSpinner').classList.add('hidden');
    }

    showError(message) {
        alert('Erreur: ' + message);
    }

    showSuccess(message) {
        alert('Succès: ' + message);
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialiser le chatbot quand la page est chargée
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new Chatbot();
});