from dishka import Provider, Scope, provide
from src.infrastructure.postgres.repositories.chat import ChatDBGateWay
from src.services.chat import ChatService


class ChatProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def chat_service(self, chat_gateway: ChatDBGateWay) -> ChatService:
        return ChatService(chat_gateway=chat_gateway)
