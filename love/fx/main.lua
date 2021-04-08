--! file: main.lua
function love.load()
    Object = require "classic"
    require "player"
    love.mouse.setRelativeMode(true)
    player = Player()
end

function love.update(dt)
    player:update(dt)
end

function love.mousemoved(x, y, dx, dy)
  player:mousemoved(x, y, dx, dy)
end
  
function love.draw()
    player:draw()
end
