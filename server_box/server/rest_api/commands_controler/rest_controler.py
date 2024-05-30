""" REST controller for orchestrator commands management ressource """
import logging
from flask import abort
from flask.views import MethodView
from flask_smorest import Blueprint
from server.orchestrator.commands import orchestrator_commands_service
from .rest_model import CommandsListSchema, CommandsQuerySchema
from server.common.box_status import box_sleeping

logger = logging.getLogger(__name__)

bp = Blueprint("commands", __name__, url_prefix="/commands")
""" The api blueprint. Should be registered in app main api object """


@bp.route("/")
class CommandsListApi(MethodView):
    """API to retrieve the available commands"""

    @box_sleeping
    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=CommandsListSchema)
    def get(self):
        """Get commands list"""
        logger.info(f"GET commands/")
        commands = orchestrator_commands_service.get_commands_list()
        return {"commands": commands}

@bp.route("/current")
class CurrentCommandsListApi(MethodView):
    """API to retrieve the current commands"""

    @box_sleeping
    @bp.doc(
        security=[{"tokenAuth": []}],
        responses={400: "BAD_REQUEST", 404: "NOT_FOUND"},
    )
    @bp.response(status_code=200, schema=CommandsListSchema)
    def get(self):
        """Get commands list"""
        logger.info(f"GET commands/current")
        commands = orchestrator_commands_service.get_current_commands()
        return {"commands": commands}

    @box_sleeping
    @bp.doc(security=[{"tokenAuth": []}], responses={400: "BAD_REQUEST"})
    @bp.arguments(CommandsQuerySchema, location="query")
    @bp.response(status_code=200, schema=CommandsListSchema)
    def post(self, args: CommandsQuerySchema):
        """
        Set current commands
        """
        logger.info(f"POST commands/current")
        _ids = args["commands_ids"].replace("[","").replace("]","").split(",")
        commands_ids = [int(_id) for _id in _ids]
        logger.info(f"Setting commands: {commands_ids}")
        if not orchestrator_commands_service.set_commands(commands_id_list=commands_ids):
            abort(400)
        commands = orchestrator_commands_service.get_current_commands()
        return {"commands": commands}

