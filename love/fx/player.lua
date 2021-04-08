--! file: player.lua
Player = Object:extend()

function Player:new()
    self.x = 300
    self.y = 20
    self.body = love
    self.speed = 500
    self.radius = 20
    self.resolution = 100
    self.sensitivity = 0.001
    self.mouseX = 0
    self.rotationAngle = 0
    self.aimLength = 60
end

function Player:update(dt)

  --! key input
  
  x_dir = bool_to_number(love.keyboard.isDown("right")) - bool_to_number(love.keyboard.isDown("left")) 
  y_dir = bool_to_number(love.keyboard.isDown("down")) - bool_to_number(love.keyboard.isDown("up")) 


  self.x = self.x + x_dir * self.speed * dt
  self.y = self.y + y_dir * self.speed * dt

  --! self.rotationAngle = self.rotationAngle + x_change * self.sensitivity
  print(self.rotationAngle)
end

function bool_to_number(value)
  return value and 1 or 0
end


function Player:draw()
    love.graphics.circle("fill",self.x, self.y, self.radius, self.resolution)
    love.graphics.line(self.x, self.y, self.x + math.cos(self.rotationAngle) * self.aimLength , self.y + math.sin(self.rotationAngle) * self.aimLength)
end
