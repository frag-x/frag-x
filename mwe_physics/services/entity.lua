-- entity.lua

local input_service = require('services/input')
local entity_service = {}

-- The entity that we control and emit updates for
entity_service.player_id = nil
-- All player entities
entity_service.entities = {}

entity_service.spawn = function(player_id, x_pos, y_pos, world)
  local colors = {
    {1, 0, 0, 1},
    {0, 1, 0, 1},
    {0, 0, 1, 1},
    {0, 1, 1, 1},
    {1, 0, 1, 1},
    {1, 1, 0, 1},
    {1, 1, 1, 1}
  }

  local shapes = {
    love.physics.newPolygonShape(25, 0, 50, 50, 0, 50),
    love.physics.newPolygonShape(0, 0, 50, 0, 50, 50, 0, 50),
    love.physics.newPolygonShape(12, 0, 36, 0, 49, 15, 49, 33, 36, 49, 12, 49, 0, 33, 0, 15)
  }
  local shape = shapes[(tonumber(player_id) % #shapes) + 1]
  local color = colors[(tonumber(player_id) % #colors) + 1]
  local body = love.physics.newBody(world, 0, 0, "dynamic") 

  local fixture = love.physics.newFixture(body, shape, 1) 
  fixture:setRestitution(0.3) 

  return {
    -- Calling tonumber() to make player_id a number instead of a string so we can do math on it
    color = color,
    id = player_id,
    shape = shape,
    x_pos = x_pos,
    y_pos = y_pos,
    body = body,
    fixture = fixture
  }
end

entity_service.draw = function(entity)
  love.graphics.setColor(entity.color)
  local points = { entity.shape:getPoints() }
  for idx, point in ipairs(points) do
    if idx % 2 == 1 then
      points[idx] = point + entity.x_pos
    else
      points[idx] = point + entity.y_pos
    end
  end
  love.graphics.polygon('line', points)
end

entity_service.move = function()
  local player = entity_service.entities[entity_service.player_id]


  xDir = bool_to_number(input_service.right) - bool_to_number(input_service.left) 
  yDir = bool_to_number(input_service.down) - bool_to_number(input_service.up) 

  player.body:applyForce(100 * xDir, 100 * yDir)

  player.x_pos = player.body:getX()
  player.y_pos = player.body:getY()

end


function bool_to_number(value)
  return value and 1 or 0
end

return entity_service
