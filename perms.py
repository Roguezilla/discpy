from discpy.discpy import DiscPy, Message


async def basic_perms_check(self: DiscPy, msg: Message):
    return await self.has_permissions(msg, self.Permissions.MANAGE_MESSAGES)

async def basic_perms_check2(self: DiscPy, msg: Message):
    return await self.has_permissions(msg, self.Permissions.MANAGE_MESSAGES) or self.is_owner(msg.author.id)
