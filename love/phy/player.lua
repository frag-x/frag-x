--! file: player.lua
Player = Object:extend()

function Player:new(world, scr_w, scr_h, radius, speed)

    -- Give the player physics

    self.body = love.physics.newBody(world, scr_w/2, scr_h/2, "dynamic") 
    self.shape = love.physics.newCircleShape( 20) 
    self.fixture = love.physics.newFixture(self.body, self.shape, 1) 
    self.fixture:setRestitution(0.3) --let the ball bounce

    -- Players settings

    self.speed = speed
    self.radius = radius
    self.resolution = 100
    self.sensitivity = 0.001
    self.mouseX = 0
    self.rotationAngle = 0
    self.aimLength = 60
end

function Player:update(dt)

  --! key input
  
  x_dir = bool_to_number(love.keyboard.isDown("d")) - bool_to_number(love.keyboard.isDown("a")) 
  y_dir = bool_to_number(love.keyboard.isDown("s")) - bool_to_number(love.keyboard.isDown("w")) 

    self.body:applyForce(self.speed * x_dir, self.speed * y_dir)
end


function Player:mousemoved(x, y, dx, dy)
  self.rotationAngle = self.rotationAngle + dx * self.sensitivity
end

function bool_to_number(value)
  return value and 1 or 0
end


function Player:draw()
    love.graphics.circle("fill",self.x, self.y, self.radius, self.resolution)
    love.graphics.line(self.x, self.y, self.x + math.cos(self.rotationAngle) * self.aimLength , self.y + math.sin(self.rotationAngle) * self.aimLength)
end

