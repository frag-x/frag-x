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

function love.mousemoved(X,Y,DX,DY)
  x,y,dx,dy = X,Y,DX,DY
  player.rotationAngle = player.rotationAngle + dx * player.sensitivity
end

function love.draw()
    player:draw()
end
